import org.arl.fjage.RealTimePlatform
import org.arl.unet.sim.channels.Mission2013a

platform = RealTimePlatform
channel = [ model: Mission2013a ]
origin = [1.217, 103.743]

simulate {
  Mission2013a.nodes.each { addr ->
    node "$addr", location: Mission2013a.nodeLocation[addr], web: 8000+addr, api: 1100+addr, stack: "$home/etc/setup"
  }
}
