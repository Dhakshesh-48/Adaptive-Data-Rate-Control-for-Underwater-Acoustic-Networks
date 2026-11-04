def loader = new GroovyClassLoader(this.class.classLoader)
def configClass = loader.parseClass(new File('classes/ExperimentConfig.groovy'))
def controllerClass = loader.parseClass(new File('classes/AdaptiveRateController.groovy'))
def expectIllegal = { Closure work ->
  boolean failed = false
  try { work.call() } catch (IllegalArgumentException ignored) { failed = true }
  assert failed
}
def base = [
  ADR_MODE:'proposed', ADR_SCENARIO:'moderate', ADR_DEPTH_CASE:'depth15',
  ADR_SEED:'1', ADR_OUTPUT_DIR:'tmp/controller-test', ADR_MEASUREMENT_S:'300',
  ADR_WEIGHTS:'0.10,0.60,0.15,0.15', ADR_RTT_REFERENCE_MS:'10000',
  ADR_HEALTHY_THRESHOLD:'0.50', ADR_POOR_THRESHOLD:'0.70',
  ADR_RELIABILITY_FLOOR:'0.50', ADR_PROBE_MARGIN:'0.01'
]
def config = configClass.fromEnv(base)
assert config.candidateIntervalsMs == [2000,2250,2500,2700,3000,3375,3750,4500,6000]
assert config.ackTimeoutMs == 30000
assert config.feedbackWaitMs == 20000 && config.feedbackRetryMs == 10000 && config.feedbackTerminalMs == 10000
assert config.reliabilityFloor == 0.50d && config.probeMargin == 0.01d
assert config.retryEveryNew == 3 && config.maxRetriesPerWindow == 2
assert config.protocolVersion == '3'

[['ADR_MODE','bad'], ['ADR_SCENARIO','bad'], ['ADR_DEPTH_CASE','bad']].each { key, value ->
  def invalid = new LinkedHashMap(base); invalid[key] = value
  expectIllegal { configClass.fromEnv(invalid) }
}
def invalidWeights = new LinkedHashMap(base); invalidWeights.ADR_WEIGHTS = '0.2,0.2,0.2,0.2'
expectIllegal { configClass.fromEnv(invalidWeights) }
def invalidCandidates = new LinkedHashMap(base); invalidCandidates.ADR_CANDIDATE_INTERVALS_MS = '3000,2700'
expectIllegal { configClass.fromEnv(invalidCandidates) }
def invalidRetryEvery = new LinkedHashMap(base); invalidRetryEvery.ADR_RETRY_EVERY_NEW = '0'
expectIllegal { configClass.fromEnv(invalidRetryEvery) }
def invalidRetryCap = new LinkedHashMap(base); invalidRetryCap.ADR_MAX_RETRIES_PER_WINDOW = '-1'
expectIllegal { configClass.fromEnv(invalidRetryCap) }

def metric = { int delivered, int duration, double loss=0.10d, double rtt=1000d, int interval=3000 ->
  [resolved:true, sent:10, delivered:delivered, pdr:delivered/10d, lossRatio:loss,
   ackRatio:0.9d, timeoutRatio:0.1d, meanRttMs:rtt, sendDurationMs:duration, intervalMs:interval]
}
def controller = controllerClass.newInstance(config)
def first = controller.observe(metric(8, 30000))
assert first.action == 'accumulate' && first.intervalMs == 3000
def baseline = controller.observe(metric(8, 30000))
assert baseline.action == 'probe-faster' && baseline.intervalMs == 2700
assert baseline.phase == 'probe'
controller.observe(metric(9, 27000, 0.10d, 1000d, 2700))
def accepted = controller.observe(metric(9, 27000, 0.10d, 1000d, 2700))
assert accepted.action == 'accept-probe' && accepted.incumbentIntervalMs == 2700
assert accepted.intervalMs == 2500 && accepted.phase == 'probe'

def rejecting = controllerClass.newInstance(config)
rejecting.observe(metric(9,30000)); rejecting.observe(metric(9,30000))
rejecting.observe(metric(8,27000,0.20d,1000d,2700))
def rejected = rejecting.observe(metric(8,27000,0.20d,1000d,2700))
assert rejected.action == 'reject-probe' && rejected.intervalMs == 3000
assert rejected.cooldownEpochs == 2

def safety = controllerClass.newInstance(config)
def slowed = safety.observe(metric(2,30000,0.80d,10000d,3000))
assert slowed.action == 'safety-slowdown' && slowed.intervalMs == 3375
assert safety.observeUnresolved().action == 'unresolved'

def reset = controllerClass.newInstance(config)
assert reset.observe(metric(8,30000)).action == 'accumulate'
reset.observeUnresolved()
assert reset.observe(metric(8,30000)).action == 'accumulate'

println 'CONTROLLER_TEST_PASS'
