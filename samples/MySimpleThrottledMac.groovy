import org.arl.fjage.*
import org.arl.fjage.param.Parameter
import org.arl.unet.*
import org.arl.unet.mac.*
import org.arl.unet.phy.*
import groovy.transform.CompileStatic

@CompileStatic
class MySimpleThrottledMac extends UnetAgent {

  private final static double TARGET_LOAD = 0.5
  private final static int    MAX_QUEUE_LEN = 16

  private AgentID phy
  boolean busy = false
  Long t0 = null
  Long t1 = null
  int waiting = 0

  @Override void setup()   { register Services.MAC }
  @Override void startup() { phy = agentForService(Services.PHYSICAL) }   // lookup after services are advertised

  @Override
  Message processRequest(Message msg) {
    switch (msg) {
      case ReservationReq:
        ReservationReq req = (ReservationReq)msg
        if (req.duration <= 0) return new RefuseRsp(req, 'Bad reservation duration')
        if (waiting >= MAX_QUEUE_LEN) return new RefuseRsp(req, 'Queue full')
        ReservationStatusNtf ntf1 = new ReservationStatusNtf(
          recipient: req.sender, inReplyTo: req.messageID, to: req.to,
          status: ReservationStatus.START)
        ReservationStatusNtf ntf2 = new ReservationStatusNtf(
          recipient: req.sender, inReplyTo: req.messageID, to: req.to,
          status: ReservationStatus.END)
        AgentLocalRandom rnd = AgentLocalRandom.current()                 // repeatable in discrete-event simulation
        double backoff = rnd.nextExp(TARGET_LOAD/req.duration/nodes)      // rate chosen to hit the target load
        long t = currentTimeMillis()
        if (t0 == null || t0 < t) t0 = t
        t0 += Math.round(1000*backoff)
        if (t0 < t1) t0 = t1
        long duration = Math.round(1000*req.duration)
        t1 = t0 + duration
        waiting++
        add new WakerBehavior(t0-t, {                                     // START after backoff, END after duration
          send ntf1
          busy = true
          waiting--
          add new WakerBehavior(duration, { send ntf2; busy = false })
        })
        return new ReservationRsp(req)
      case ReservationCancelReq:
      case ReservationAcceptReq:
      case TxAckReq:
        return new RefuseRsp(msg, 'Not supported')
    }
    return null
  }

  @Override
  List<Parameter> getParameterList() {
    return allOf(MacParam, Param)
  }

  enum Param implements Parameter { nodes }                              // one user-configurable parameter

  int nodes = 6                            // number of nodes, set by the user
  final int reservationPayloadSize = 0
  final int ackPayloadSize = 0
  final float maxReservationDuration = Float.POSITIVE_INFINITY

  boolean getChannelBusy() { return busy }                               // reflects the real reservation state

  float getRecommendedReservationDuration() {                            // assume one frame per reservation
    return (float)get(phy, Physical.DATA, PhysicalChannelParam.frameDuration)
  }

}
