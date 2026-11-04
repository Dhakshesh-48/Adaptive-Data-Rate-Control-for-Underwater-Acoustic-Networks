import org.arl.fjage.RealTimePlatform
import org.arl.unet.sim.channels.ProtocolChannelModel

platform = RealTimePlatform                 // use real-time mode
origin = [1.216, 103.851]                   // applies to all nodes

channel.model = ProtocolChannelModel        // deterministic delivery (see channel models)

simulate {
  node 'A', location: [121.m,  137.m, -10.m], web: 8081, api: 1101, stack: "$home/etc/setup"
  node 'B', location: [160.m, -232.m, -15.m], web: 8082, api: 1102, stack: "$home/etc/setup"
  node 'C', location: [651.m,  140.m,  -5.m], web: 8083, api: 1103, stack: "$home/etc/setup"
}
