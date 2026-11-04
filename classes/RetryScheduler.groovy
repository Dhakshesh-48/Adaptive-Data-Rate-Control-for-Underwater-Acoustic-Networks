class RetryScheduler {
  final int retryEveryNew
  final int maxRetriesPerWindow
  int originalsSinceRetry = 0
  Integer activeWindowInterval = null
  List<Map> queue = []
  Set<Integer> queued = [] as Set<Integer>
  Set<Integer> attempted = [] as Set<Integer>
  Map<Integer,Integer> reservedByWindow = [:].withDefault { 0 }

  RetryScheduler(int retryEveryNew, int maxRetriesPerWindow) {
    if (retryEveryNew <= 0) throw new IllegalArgumentException('retryEveryNew must be positive')
    if (maxRetriesPerWindow < 0) throw new IllegalArgumentException('maxRetriesPerWindow must be nonnegative')
    this.retryEveryNew = retryEveryNew
    this.maxRetriesPerWindow = maxRetriesPerWindow
  }

  boolean ackRequested(String mode, int position, int windowSize, int attempt) {
    if (position <= 0 || windowSize <= 0 || position > windowSize || attempt <= 0) {
      throw new IllegalArgumentException('Invalid ACK policy input')
    }
    attempt > 1 || mode != 'proposed' || position > windowSize - 2
  }

  List<Integer> enqueue(int windowId, int destination, Collection<Integer> missing) {
    if (windowId <= 0 || destination <= 0) throw new IllegalArgumentException('Invalid retry identity')
    int remaining = maxRetriesPerWindow - reservedByWindow[windowId]
    if (remaining <= 0) return []
    List<Integer> added = []
    missing.toSet().sort().each { int seq ->
      if (remaining > 0 && seq > 0 && !queued.contains(seq) && !attempted.contains(seq)) {
        queue << [windowId:windowId, destination:destination, seq:seq, attempt:2]
        queued << seq
        added << seq
        reservedByWindow[windowId] = reservedByWindow[windowId] + 1
        remaining--
      }
    }
    added.asImmutable()
  }

  int intervalForOpportunity(int proposedInterval) {
    if (proposedInterval <= 0) throw new IllegalArgumentException('Interval must be positive')
    activeWindowInterval == null ? proposedInterval : activeWindowInterval
  }

  void noteOriginal(int position, int windowSize, int usedInterval) {
    if (position <= 0 || windowSize <= 0 || position > windowSize || usedInterval <= 0) {
      throw new IllegalArgumentException('Invalid original pacing input')
    }
    if (position == 1) activeWindowInterval = usedInterval
    if (activeWindowInterval == null || activeWindowInterval != usedInterval) {
      throw new IllegalArgumentException('Interval changed within scheduler window')
    }
    originalsSinceRetry++
    if (position == windowSize) activeWindowInterval = null
  }

  void noteOriginal() { originalsSinceRetry++ }

  Map takeRetry(boolean allowed) {
    if (!allowed || queue.isEmpty() || originalsSinceRetry < retryEveryNew) return null
    Map item = queue.remove(0)
    queued.remove(item.seq as int)
    attempted << (item.seq as int)
    originalsSinceRetry = 0
    item.asImmutable()
  }

  int queuedCount() { queue.size() }
}
