boolean loadAgentByClass(String name, String clazz) {
  try {
    container.add name, Class.forName(clazz).newInstance()
    return true
  } catch (Exception ex) {
    return false
  }
}

boolean loadAgentByClass(String name, String... clazzes) {
  for (String clazz: clazzes) {
    if (loadAgentByClass(name, clazz)) return true
  }
  return false
}

loadAgentByClass 'arp',          'org.arl.unet.addr.AddressResolution'
loadAgentByClass 'ranging',      'org.arl.unet.localization.Ranging'
loadAgentByClass 'mac',          'org.arl.unet.mac.CSMA'
loadAgentByClass 'uwlink',       'org.arl.unet.link.ECLink'
loadAgentByClass 'router',       'org.arl.unet.net.Router'
loadAgentByClass 'rdp',          'org.arl.unet.net.RouteDiscoveryProtocol'
loadAgentByClass 'caddy',        'org.arl.unet.transport.Caddy', 'org.arl.unet.transport.CaddyLite'
loadAgentByClass 'profiles',     'org.arl.unet.profiles.Profiles'
loadAgentByClass 'speedtest',    'org.arl.unet.utils.SpeedTest'
loadAgentByClass 'scheduler',    'org.arl.unet.scheduler.Scheduler'
loadAgentByClass 'diag',         'org.arl.unet.utils.Diagnostics'

container.add 'bbmon',  new org.arl.unet.bb.BasebandSignalMonitor(new File(home, 'logs/signals-0.txt').path)


container.add 'experiment', new AdaptiveExperimentAgent(ExperimentConfig.fromEnv(System.getenv()))

