import org.arl.fjage.*
import org.arl.fjage.param.Parameter
import org.arl.unet.*
import org.arl.unet.mac.*
import groovy.transform.CompileStatic

@CompileStatic
class MySimplestMac extends UnetAgent {

  @Override
  void setup() {
    register Services.MAC                  // advertise the MAC service
  }

  @Override
  Message processRequest(Message msg) {
    switch (msg) {
      case ReservationReq:
        ReservationReq req = (ReservationReq)msg
        if (req.duration <= 0) return new RefuseRsp(req, 'Bad reservation duration')
        ReservationStatusNtf ntf1 = new ReservationStatusNtf(
          recipient: req.sender, inReplyTo: req.messageID, to: req.to,
          status: ReservationStatus.START)
        ReservationStatusNtf ntf2 = new ReservationStatusNtf(
          recipient: req.sender, inReplyTo: req.messageID, to: req.to,
          status: ReservationStatus.END)
        add new OneShotBehavior({ send ntf1 })                       // START immediately
        add new WakerBehavior(Math.round(1000*req.duration), {       // END after duration
          send ntf2
        })
        return new ReservationRsp(req)     // defaults to an AGREE performative
      case ReservationCancelReq:
      case ReservationAcceptReq:
      case TxAckReq:
        return new RefuseRsp(msg, 'Not supported')
    }
    return null                            // NOT_UNDERSTOOD for anything else
  }

  @Override
  List<Parameter> getParameterList() {
    return allOf(MacParam)                 // advertise MAC service parameters
  }

  final boolean channelBusy = false        // 'final' makes parameters read-only
  final int reservationPayloadSize = 0
  final int ackPayloadSize = 0
  final float maxReservationDuration = Float.POSITIVE_INFINITY
  final Float recommendedReservationDuration = null

}
