import org.arl.fjage.*
import org.arl.unet.*
import org.arl.unet.nodeinfo.NodeInfoParam

class AdaptiveRateAgent extends UnetAgent {

  boolean adaptive = true

  AgentID transport
  int addr = 0

  int seq = 0
  int sent = 0
  int acked = 0
  int lost = 0

  int intervalMs = 3000
  final int MIN_INTERVAL_MS = 1000
  final int MAX_INTERVAL_MS = 10000
  final int FIXED_INTERVAL_MS = 3000
  final int TIMEOUT_MS = 12000

  Map<Integer, Long> pending = [:]

  AdaptiveRateAgent(boolean adaptive) {
    this.adaptive = adaptive
  }

  @Override
  void startup() {
    transport = agentForService(Services.TRANSPORT)
    subscribe topic(Topics.DATAGRAM)

    add new OneShotBehavior({
      def ni = agentForService(Services.NODE_INFO)
      addr = (int)get(ni, NodeInfoParam.address)

      if (addr == 1) {
        println "Sender ready. Mode: ${adaptive ? 'ADAPTIVE' : 'FIXED'}"
        add new WakerBehavior(3000, { sendPacket() })
      } else {
        println "Receiver ready."
      }
    })
  }

  void sendPacket() {
    if (addr != 1) return

    if (!adaptive) intervalMs = FIXED_INTERVAL_MS

    seq++
    sent++
    long sentAt = currentTimeMillis()
    pending[seq] = sentAt

    // Fixed-size data payload (64 bytes)
    String payload = "D:${seq}".padRight(64, 'x')

    send new DatagramReq(
      recipient: transport,
      to: (seq % 2 == 0 ? 2 : 3),
      protocol: Protocol.USER,
      data: payload.bytes
    )

    logRow('SEND', seq, -1)

    int thisSeq = seq
    add new WakerBehavior(TIMEOUT_MS, {
      if (pending.remove(thisSeq) != null) {
        lost++

        if (adaptive) {
          intervalMs = Math.min(
            MAX_INTERVAL_MS,
            Math.max(MIN_INTERVAL_MS, (int)(intervalMs * 1.5))
          )
        }

        logRow('TIMEOUT', thisSeq, -1)
        println "Timeout seq=${thisSeq}, lost=${lost}, interval=${intervalMs}ms"
      }
    })

    add new WakerBehavior(intervalMs, { sendPacket() })
  }

  @Override
  void processMessage(Message msg) {
    if (!(msg instanceof DatagramNtf)) return
    if (msg.protocol != Protocol.USER) return

    String payload = new String(msg.data, 'UTF-8').replaceAll('x+$', '')

    if (payload.startsWith('D:') && (addr == 2 || addr == 3)) {
println "Node ${addr} received packet: ${payload}"
      int receivedSeq = payload.substring(2).toInteger()

      send new DatagramReq(
        recipient: transport,
        to: 1,
        protocol: Protocol.USER,
        data: "A:${receivedSeq}".bytes
      )
      return
    }

    if (payload.startsWith('A:') && addr == 1) {
      int ackSeq = payload.substring(2).toInteger()
      Long started = pending.remove(ackSeq)

      if (started == null) return

      long rtt = currentTimeMillis() - started
      acked++

      if (adaptive) {
        double lossRatio = sent > 0 ? lost / (double)sent : 0

        if (rtt > 3500 || lossRatio > 0.10) {
          intervalMs = Math.min(
            MAX_INTERVAL_MS, (int)(intervalMs * 1.25)
          )
        } else {
          intervalMs = Math.max(
            MIN_INTERVAL_MS, (int)(intervalMs * 0.90)
          )
        }
      }

      logRow('ACK', ackSeq, rtt)
      println "ACK seq=${ackSeq}, RTT=${rtt}ms, interval=${intervalMs}ms"
    }
  }

  void logRow(String event, int packetSeq, long rtt) {
    File f = new File(adaptive ? 'results/metrics.csv' : 
'results/fixed-first-run.csv')
    f.parentFile.mkdirs()

    if (!f.exists()) {
      f.text = 'event,mode,seq,time_ms,rtt_ms,interval_ms,sent,acked,lost\n'
    }

    f.append(
      "${event},${adaptive ? 'adaptive' : 'fixed'}," +
      "${packetSeq},${currentTimeMillis()},${rtt < 0 ? '' : rtt}," +
      "${intervalMs},${sent},${acked},${lost}\n"
    )
  }
}
