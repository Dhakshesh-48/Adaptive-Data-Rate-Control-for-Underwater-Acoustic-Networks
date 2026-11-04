import org.arl.unet.sim.Reception
import org.arl.unet.sim.channels.ProtocolChannelModel

class ScenarioChannelModel extends ProtocolChannelModel {
  String scenario
  ScenarioChannelModel(String scenario=(System.getenv('ADR_SCENARIO') ?: 'moderate')) {
    this.scenario=scenario
    communicationRange=3000f; detectionRange=3500f; interferenceRange=4000f; soundSpeed=1500f
  }
  Map probabilitiesAt(long simulatedMs) {
    switch(scenario) {
      case 'good': return [detection:0.995f, decoding:0.995f]
      case 'moderate': return [detection:0.96f, decoding:0.94f]
      case 'poor': return [detection:0.85f, decoding:0.75f]
      case 'step':
        return simulatedMs < 120000L || simulatedMs >= 240000L ?
          [detection:0.995f, decoding:0.995f] : [detection:0.85f, decoding:0.75f]
      default: throw new IllegalArgumentException('Unsupported scenario')
    }
  }
  @Override protected float getProbabilityDetection(Reception rx) { probabilitiesAt(rx.rxStartTime as long).detection as float }
  @Override protected float getProbabilityDecoding(Reception rx) { probabilitiesAt(rx.rxStartTime as long).decoding as float }
}
