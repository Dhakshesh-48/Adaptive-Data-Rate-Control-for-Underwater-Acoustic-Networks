import com.google.gson.GsonBuilder
import org.arl.fjage.*
import org.arl.unet.sim.channels.*

def config=ExperimentConfig.fromEnv(System.getenv())
AgentLocalRandom.setRootSeed(config.seed)
channel.model=ScenarioChannelModel
modem.dataRate=[2400,2400].bps
modem.frameLength=[256,256].bytes
modem.headerLength=0
modem.preambleDuration=0
modem.txDelay=0
long totalSeconds=60L+config.measurementSeconds+Math.ceil(2d*Math.max(config.ackTimeoutMs,config.reportTimeoutMs)/1000d) as long
int durationMs=(int)(totalSeconds*1000L)

simulate durationMs, {
  node 'A',address:1,location:[0.km,0.km,-15.m],stack:"$home/scripts/adaptive-setup-a.groovy"
  node 'B',address:2,location:[1.km,0.km,-15.m],stack:"$home/scripts/adaptive-setup-b.groovy"
  node 'C',address:3,location:[2.km,0.km,-config.depthMeters.m],stack:"$home/scripts/adaptive-setup-b.groovy"
}

config.outputDir.mkdirs()
def manifest=config.toManifestMap()+[status:'complete',simulated_total_s:totalSeconds,unet_version:'7.0.0',java_version:System.getProperty('java.version')]
new File(config.outputDir,'manifest.json').text=new GsonBuilder().setPrettyPrinting().create().toJson(manifest)
println "EXPERIMENT_COMPLETE ${config.outputDir}"
