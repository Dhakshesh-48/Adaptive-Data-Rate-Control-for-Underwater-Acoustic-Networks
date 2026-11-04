import org.arl.fjage.*
import org.arl.fjage.groovy.FSMBuilder
import org.arl.fjage.param.Parameter
import org.arl.unet.*
import org.arl.unet.mac.*
import org.arl.unet.phy.*
import org.arl.unet.nodeinfo.NodeInfoParam
import groovy.transform.*

@CompileStatic
class MySimpleHandshakeMac extends UnetAgent {

  ////// protocol constants

  int PROTOCOL = Protocol.MAC

  float RTS_BACKOFF    = 2     // seconds
  float CTS_TIMEOUT    = 5     // seconds
  float BACKOFF_RANDOM = 5     // seconds
  float MAX_PROP_DELAY = 2     // seconds

  int MAX_RETRY     = 3
  int MAX_QUEUE_LEN = 16

  ////// reservation request queue

  Queue<ReservationReq> queue = new ArrayDeque<ReservationReq>(MAX_QUEUE_LEN)

  ////// PDU encoder/decoder

  int RTS_PDU = 0x01
  int CTS_PDU = 0x02

  PDU pdu = PDU.withFormat {
    uint8('type')         // RTS_PDU / CTS_PDU
    uint16('duration')    // ms
  }

  ////// protocol FSM

  enum State { IDLE, RTS, TX, RX, BACKOFF }
  enum Event { RX_RTS, RX_CTS, SNOOP_RTS, SNOOP_CTS }

  FSMBehavior fsm = buildFSM()

  private FSMBehavior buildFSM() {
    return FSMBuilder.build {

      int retryCount = 0
      double backoff = 0
      Map rxInfo
      def rnd = AgentLocalRandom.current()

      state(State.IDLE) {
        action {
          if (!queue.isEmpty()) {
            after(rnd.nextDouble(0, BACKOFF_RANDOM)) { setNextState(State.RTS) }
          }
          block()
        }
        onEvent(Event.RX_RTS)    { Map info -> rxInfo = info; setNextState(State.RX) }
        onEvent(Event.SNOOP_RTS) { backoff = RTS_BACKOFF; setNextState(State.BACKOFF) }
        onEvent(Event.SNOOP_CTS) { Map info ->
          backoff = (double)info.duration + 2*MAX_PROP_DELAY
          setNextState(State.BACKOFF)
        }
      }

      state(State.RTS) {
        onEnter {
          ReservationReq msg = queue.peek()
          def bytes = pdu.encode(type: RTS_PDU, duration: Math.ceil(msg.duration*1000))
          phy << new TxFrameReq(to: msg.to, type: Physical.CONTROL, protocol: PROTOCOL, data: bytes)
          after(CTS_TIMEOUT) {
            if (++retryCount >= MAX_RETRY) {
              sendReservationStatusNtf(queue.poll(), ReservationStatus.FAILURE)
              retryCount = 0
            }
            setNextState(State.IDLE)
          }
        }
        onEvent(Event.RX_CTS) { setNextState(State.TX) }
      }

      state(State.TX) {
        onEnter {
          ReservationReq msg = queue.poll()
          retryCount = 0
          sendReservationStatusNtf(msg, ReservationStatus.START)
          after(msg.duration) {
            sendReservationStatusNtf(msg, ReservationStatus.END)
            setNextState(State.IDLE)
          }
        }
      }

      state(State.RX) {
        onEnter {
          def bytes = pdu.encode(type: CTS_PDU, duration: Math.round((double)rxInfo.duration*1000))
          phy << new TxFrameReq(to: (int)rxInfo.from, type: Physical.CONTROL, protocol: PROTOCOL, data: bytes)
          after((double)rxInfo.duration + 2*MAX_PROP_DELAY) { setNextState(State.IDLE) }
          rxInfo = null
        }
      }

      state(State.BACKOFF) {
        onEnter { after(backoff) { setNextState(State.IDLE) } }
        onEvent(Event.SNOOP_RTS) { backoff = RTS_BACKOFF; reenterState() }
        onEvent(Event.SNOOP_CTS) { Map info ->
          backoff = (double)info.duration + 2*MAX_PROP_DELAY
          reenterState()
        }
      }

    }
  }

  ////// agent startup sequence

  AgentID phy
  int addr

  @Override
  void setup() {
    register Services.MAC
  }

  @Override
  void startup() {
    phy = agentForService(Services.PHYSICAL)
    subscribe topic(phy)                  // overheard (snooped) frames
    subscribe topic(Topics.DATAGRAM)      // frames addressed to this node
    add new OneShotBehavior({
      def nodeInfo = agentForService(Services.NODE_INFO)
      addr = (int)get(nodeInfo, NodeInfoParam.address)
    })
    add(fsm)
  }

  ////// process MAC service requests

  @Override
  Message processRequest(Message msg) {
    switch (msg) {
      case ReservationReq:
        ReservationReq req = (ReservationReq)msg
        if (req.to == Address.BROADCAST || req.to == addr)
          return new RefuseRsp(req, 'Reservation must have a destination node')
        if (req.duration <= 0 || req.duration > maxReservationDuration)
          return new RefuseRsp(req, 'Bad reservation duration')
        if (queue.size() >= MAX_QUEUE_LEN)
          return new RefuseRsp(req, 'Queue full')
        queue.add(req)
        fsm.restart()    // wake the fsm, which blocks when the queue is empty
        return new ReservationRsp(req)
      case ReservationCancelReq:
      case ReservationAcceptReq:
      case TxAckReq:
        return new RefuseRsp(msg, 'Not supported')
    }
    return null
  }

  ////// handle incoming MAC PDUs

  @Override
  void processMessage(Message msg) {
    if (msg instanceof RxFrameNtf && msg.protocol == PROTOCOL) {
      def rx = pdu.decode(msg.data)
      def info = [from: msg.from, to: msg.to, duration: ((int)rx.duration)/1000.0d]
      if (rx.type == RTS_PDU)
        fsm.trigger(info.to == addr ? Event.RX_RTS : Event.SNOOP_RTS, info)
      else if (rx.type == CTS_PDU)
        fsm.trigger(info.to == addr ? Event.RX_CTS : Event.SNOOP_CTS, info)
    }
  }

  ////// expose parameters expected of a MAC service

  @Override
  List<Parameter> getParameterList() {
    return allOf(MacParam)
  }

  final int reservationPayloadSize = 0
  final int ackPayloadSize = 0
  final float maxReservationDuration = 65.535    // uint16 ms field in the PDU
  final Float recommendedReservationDuration = null

  boolean getChannelBusy() {
    return fsm.currentState != State.IDLE
  }

  ////// utility methods

  private void sendReservationStatusNtf(ReservationReq msg, ReservationStatus status) {
    send new ReservationStatusNtf(
      recipient: msg.sender, inReplyTo: msg.messageID,
      to: msg.to, from: addr, status: status)
  }

}
