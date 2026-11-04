import org.arl.fjage.*
import org.arl.unet.*
import org.arl.unet.phy.*
import org.arl.unet.sim.*
import org.arl.unet.sim.channels.*

println '''
Pure ALOHA simulation
=====================

TX Count\tRX Count\tOffered Load\tThroughput
--------\t--------\t------------\t----------'''

channel.model = ProtocolChannelModel        // use the protocol channel model
modem.dataRate = [2400, 2400].bps           // arbitrary data rate
modem.frameLength = [2400/8, 2400/8].bytes  // 1 second worth of data per frame
modem.headerLength = 0                      // no header overhead
modem.preambleDuration = 0                  // no preamble overhead
modem.txDelay = 0                           // no hardware delays

def nodes = 1..4                            // 4 nodes
trace.warmup = 15.minutes                   // collect statistics after steady state

for (def load = 0.1; load <= 1.5; load += 0.1) {
  simulate 2.hours, {                       // simulate 2 hours of elapsed time
    nodes.each { myAddr ->
      def myNode = node "${myAddr}", address: myAddr, location: [0, 0, 0]
      myNode.startup = {                    // startup script run on each node
        def phy = agentForService(Services.PHYSICAL)
        def arrivalRate = load/nodes.size() // arrival rate per node
        add new PoissonBehavior((long)(1000/arrivalRate), {  // avg inter-arrival time (ms)
          def dst = rnditem(nodes-myAddr)   // random destination (excluding self)
          phy << new ClearReq()
          phy << new TxFrameReq(to: dst, type: Physical.DATA)
        })
      }
    }
  }
  println sprintf('%6d\t\t%6d\t\t%7.3f\t\t%7.3f',
    [trace.txCount, trace.rxCount, trace.offeredLoad, trace.throughput])
}
