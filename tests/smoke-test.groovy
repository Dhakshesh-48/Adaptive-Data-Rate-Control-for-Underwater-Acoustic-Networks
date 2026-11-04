assert System.getProperty('java.version').startsWith('1.8')
assert Class.forName('org.arl.unet.sim.channels.ProtocolChannelModel')
assert new File('classes').isDirectory()
println 'SMOKE_TEST_PASS'
