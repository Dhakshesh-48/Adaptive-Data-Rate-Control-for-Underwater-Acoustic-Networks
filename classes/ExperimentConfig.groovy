class ExperimentConfig {
  String mode
  String scenario
  String depthCase
  int depthMeters
  long seed
  File outputDir
  int windowSize
  int ackTimeoutMs
  int reportTimeoutMs
  int feedbackWaitMs
  int feedbackRetryMs
  int feedbackTerminalMs
  int finalFeedbackWaitMs
  int measurementSeconds
  int initialIntervalMs = 3000
  int fixedIntervalMs = 3000
  int minIntervalMs = 1000
  int maxIntervalMs = 10000
  List<Integer> candidateIntervalsMs
  double rttReferenceMs
  List<Double> weights
  double healthyThreshold
  double poorThreshold
  double reliabilityFloor
  double probeMargin
  int retryEveryNew
  int maxRetriesPerWindow
  String protocolVersion = '3'

  static ExperimentConfig fromEnv(Map env) {
    def c = new ExperimentConfig()
    c.mode = text(env, 'ADR_MODE', 'fixed')
    c.scenario = text(env, 'ADR_SCENARIO', 'moderate')
    c.depthCase = text(env, 'ADR_DEPTH_CASE', 'depth15')
    if (!(c.mode in ['fixed','legacy','proposed'])) throw new IllegalArgumentException('Unsupported mode')
    if (!(c.scenario in ['good','moderate','poor','step'])) throw new IllegalArgumentException('Unsupported scenario')
    if (!(c.depthCase in ['depth15','depth1000'])) throw new IllegalArgumentException('Unsupported depth case')
    c.depthMeters = c.depthCase == 'depth15' ? 15 : 1000
    c.seed = positiveLong(env, 'ADR_SEED', 1)
    c.outputDir = new File(text(env, 'ADR_OUTPUT_DIR', 'results/run'))
    c.windowSize = positiveInt(env, 'ADR_WINDOW_SIZE', 10)
    c.ackTimeoutMs = positiveInt(env, 'ADR_ACK_TIMEOUT_MS', 30000)
    c.reportTimeoutMs = positiveInt(env, 'ADR_REPORT_TIMEOUT_MS', 12000)
    c.feedbackWaitMs = positiveInt(env, 'ADR_FEEDBACK_WAIT_MS', 20000)
    c.feedbackRetryMs = positiveInt(env, 'ADR_FEEDBACK_RETRY_MS', 10000)
    c.feedbackTerminalMs = positiveInt(env, 'ADR_FEEDBACK_TERMINAL_MS', 10000)
    c.finalFeedbackWaitMs = positiveInt(env, 'ADR_FINAL_FEEDBACK_WAIT_MS', 2000)
    c.measurementSeconds = positiveInt(env, 'ADR_MEASUREMENT_S', 300)
    c.initialIntervalMs = positiveInt(env, 'ADR_INITIAL_INTERVAL_MS', 3000)
    c.fixedIntervalMs = positiveInt(env, 'ADR_FIXED_INTERVAL_MS', 3000)
    c.candidateIntervalsMs = text(env, 'ADR_CANDIDATE_INTERVALS_MS', '2000,2250,2500,2700,3000,3375,3750,4500,6000').split(',').collect { it.toInteger() }
    if (c.candidateIntervalsMs != c.candidateIntervalsMs.toSet().sort() || !c.candidateIntervalsMs.contains(c.initialIntervalMs)) throw new IllegalArgumentException('Candidate intervals must be unique, ascending, and contain the initial interval')
    c.rttReferenceMs = number(env, 'ADR_RTT_REFERENCE_MS', 10000d)
    if (c.rttReferenceMs <= 0) throw new IllegalArgumentException('ADR_RTT_REFERENCE_MS must be positive')
    c.healthyThreshold = number(env, 'ADR_HEALTHY_THRESHOLD', 0.50d)
    c.poorThreshold = number(env, 'ADR_POOR_THRESHOLD', 0.70d)
    if (c.healthyThreshold < 0 || c.poorThreshold > 1 || c.healthyThreshold >= c.poorThreshold) throw new IllegalArgumentException('Invalid thresholds')
    c.weights = text(env, 'ADR_WEIGHTS', '0.10,0.60,0.15,0.15').split(',').collect { it.toDouble() }
    if (c.weights.size() != 4 || c.weights.any { it < 0 } || Math.abs(c.weights.sum() - 1d) > 1e-9) throw new IllegalArgumentException('Weights must be four nonnegative values summing to one')
    c.reliabilityFloor = number(env, 'ADR_RELIABILITY_FLOOR', 0.50d)
    c.probeMargin = number(env, 'ADR_PROBE_MARGIN', 0.01d)
    c.retryEveryNew = positiveInt(env, 'ADR_RETRY_EVERY_NEW', 3)
    c.maxRetriesPerWindow = nonnegativeInt(env, 'ADR_MAX_RETRIES_PER_WINDOW', 2)
    if (c.reliabilityFloor < 0d || c.reliabilityFloor > 1d) throw new IllegalArgumentException('ADR_RELIABILITY_FLOOR must be in [0,1]')
    if (c.probeMargin < 0d) throw new IllegalArgumentException('ADR_PROBE_MARGIN must be nonnegative')
    return c
  }

  Map toManifestMap() { [protocol_version:protocolVersion, mode:mode, scenario:scenario, depth_case:depthCase, depth_m:depthMeters, seed:seed,
    window_size:windowSize, ack_timeout_ms:ackTimeoutMs, report_timeout_ms:reportTimeoutMs, feedback_wait_ms:feedbackWaitMs,
    feedback_retry_ms:feedbackRetryMs, feedback_terminal_ms:feedbackTerminalMs, final_feedback_wait_ms:finalFeedbackWaitMs,
    rtt_reference_ms:rttReferenceMs, measurement_s:measurementSeconds, initial_interval_ms:initialIntervalMs,
    fixed_interval_ms:fixedIntervalMs, candidate_intervals_ms:candidateIntervalsMs, weights:weights,
    healthy_threshold:healthyThreshold, poor_threshold:poorThreshold, reliability_floor:reliabilityFloor, probe_margin:probeMargin,
    retry_every_new:retryEveryNew, max_retries_per_window:maxRetriesPerWindow,
    ack_policy:mode == 'proposed' ? 'window-tail' : 'per-message'] }
  private static String text(Map e, String k, String d) { (e[k] ?: d).toString().trim() }
  private static int positiveInt(Map e, String k, int d) { int v=text(e,k,"$d").toInteger(); if(v<=0) throw new IllegalArgumentException("$k must be positive"); v }
  private static int nonnegativeInt(Map e, String k, int d) { int v=text(e,k,"$d").toInteger(); if(v<0) throw new IllegalArgumentException("$k must be nonnegative"); v }
  private static long positiveLong(Map e, String k, long d) { long v=text(e,k,"$d").toLong(); if(v<=0) throw new IllegalArgumentException("$k must be positive"); v }
  private static double number(Map e, String k, double d) { text(e,k,"$d").toDouble() }
}
