class AdaptiveRateController {
  def config
  int intervalMs
  int incumbentIntervalMs
  String phase = 'incumbent'
  int cooldownEpochs = 0
  Double incumbentGoodput = null
  List<Map> epoch = []

  AdaptiveRateController(config) {
    this.config = config
    intervalMs = config.initialIntervalMs
    incumbentIntervalMs = config.initialIntervalMs
  }

  Map observe(Map metrics) {
    if (!metrics.resolved || metrics.meanRttMs == null) return observeUnresolved()
    Map scored = score(metrics)
    if ((metrics.pdr as double) < config.reliabilityFloor || scored.score >= config.poorThreshold) {
      intervalMs = slower(intervalMs)
      incumbentIntervalMs = intervalMs
      incumbentGoodput = null
      phase = 'incumbent'
      cooldownEpochs = 0
      epoch.clear()
      return decision(scored, 'safety-slowdown', null)
    }
    epoch << metrics + [score:scored.score]
    if (epoch.size() < 2) return decision(scored, 'accumulate', null)

    double epochPdr = epoch.sum { it.delivered as int } / (double)epoch.sum { it.sent as int }
    double epochScore = epoch.sum { it.score as double } / epoch.size()
    double durationMs = epoch.sum { it.sendDurationMs as double }
    double goodput = durationMs ? epoch.sum { (it.delivered as int) * 64d * 8d } * 1000d / durationMs : 0d
    epoch.clear()
    if (epochPdr < config.reliabilityFloor || epochScore >= config.poorThreshold) {
      intervalMs = slower(intervalMs)
      incumbentIntervalMs = intervalMs
      incumbentGoodput = null
      phase = 'incumbent'
      cooldownEpochs = 0
      return decision(scored, 'safety-slowdown', goodput)
    }
    if (phase == 'probe') {
      boolean accepted = incumbentGoodput != null && goodput >= incumbentGoodput * (1d + config.probeMargin)
      if (accepted) {
        incumbentIntervalMs = intervalMs
        incumbentGoodput = goodput
        int next = faster(incumbentIntervalMs)
        intervalMs = next
        phase = next == incumbentIntervalMs ? 'incumbent' : 'probe'
        return decision(scored, 'accept-probe', goodput)
      }
      intervalMs = incumbentIntervalMs
      phase = 'incumbent'
      cooldownEpochs = 2
      return decision(scored, 'reject-probe', goodput)
    }

    incumbentGoodput = goodput
    if (cooldownEpochs > 0) {
      cooldownEpochs--
      if (cooldownEpochs == 0) {
        int next = faster(incumbentIntervalMs)
        intervalMs = next
        phase = next == incumbentIntervalMs ? 'incumbent' : 'probe'
        return decision(scored, phase == 'probe' ? 'probe-faster' : 'hold-boundary', goodput)
      }
      return decision(scored, 'cooldown-hold', goodput)
    }
    int next = faster(incumbentIntervalMs)
    intervalMs = next
    phase = next == incumbentIntervalMs ? 'incumbent' : 'probe'
    decision(scored, phase == 'probe' ? 'probe-faster' : 'hold-boundary', goodput)
  }

  Map observeUnresolved() {
    epoch.clear()
    [resolved:false, score:null, action:'unresolved', intervalMs:intervalMs, incumbentIntervalMs:incumbentIntervalMs,
     phase:phase, cooldownEpochs:cooldownEpochs, penalties:[:], epochGoodputBps:null]
  }

  Map evaluate(int currentIntervalMs, Map metrics) {
    intervalMs = currentIntervalMs
    observe(metrics + [resolved:metrics.meanRttMs != null, pdr:1d-(metrics.lossRatio as double),
      sent:(metrics.sent ?: 1), delivered:(metrics.delivered ?: Math.round((1d-(metrics.lossRatio as double))*(metrics.sent ?: 1))),
      sendDurationMs:(metrics.sendDurationMs ?: currentIntervalMs)])
  }

  private Map score(Map metrics) {
    List<Double> penalties = [
      Math.min((metrics.meanRttMs as double) / config.rttReferenceMs, 1d),
      metrics.lossRatio as double,
      1d - (metrics.ackRatio as double),
      metrics.timeoutRatio as double
    ]
    if (penalties.any { it < 0d || it > 1d }) throw new IllegalArgumentException('Penalty outside [0,1]')
    double score = (0..<4).sum { config.weights[it] * penalties[it] } as double
    [score:score, penalties:[rtt:penalties[0], loss:penalties[1], ackFailure:penalties[2], timeout:penalties[3]]]
  }

  private Map decision(Map scored, String action, Double goodput) {
    [resolved:true, score:scored.score, action:action, intervalMs:intervalMs,
     incumbentIntervalMs:incumbentIntervalMs, phase:phase, cooldownEpochs:cooldownEpochs,
     penalties:scored.penalties, epochGoodputBps:goodput]
  }

  private int faster(int value) {
    int i=config.candidateIntervalsMs.indexOf(value)
    i <= 0 ? config.candidateIntervalsMs[0] : config.candidateIntervalsMs[i-1]
  }

  private int slower(int value) {
    int i=config.candidateIntervalsMs.indexOf(value)
    i < 0 || i >= config.candidateIntervalsMs.size()-1 ? config.candidateIntervalsMs[-1] : config.candidateIntervalsMs[i+1]
  }
}
