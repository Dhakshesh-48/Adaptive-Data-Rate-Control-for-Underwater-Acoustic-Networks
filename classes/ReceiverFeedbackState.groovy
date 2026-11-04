class ReceiverFeedbackState {
  Map<Integer,Set<Integer>> receivedByWindow = [:].withDefault { [] as Set<Integer> }
  Map<Integer,List<Integer>> frozenSnapshots = [:]

  Map recordData(int windowId, int seq) {
    int previous = windowId - 1
    Integer frozenWindow = null
    if (previous > 0 && !frozenSnapshots.containsKey(previous)) {
      frozenSnapshots[previous] = receivedByWindow[previous].toList().sort().asImmutable()
      frozenWindow = previous
    }
    boolean wasFrozen = frozenSnapshots.containsKey(windowId)
    boolean fresh = receivedByWindow[windowId].add(seq)
    [fresh:fresh, status:wasFrozen ? 'LATE_DATA' : (fresh ? 'DELIVER' : 'DUPLICATE_DATA'), frozenWindow:frozenWindow]
  }

  Map ackSnapshot(int currentWindow) {
    int previous = currentWindow - 1
    if (previous > 0 && frozenSnapshots.containsKey(previous)) {
      return [snapshotWindow:previous, delivered:frozenSnapshots[previous]]
    }
    [snapshotWindow:null, delivered:[]]
  }

  List<Integer> snapshotForReport(int windowId) {
    if (!frozenSnapshots.containsKey(windowId)) {
      frozenSnapshots[windowId] = receivedByWindow[windowId].toList().sort().asImmutable()
    }
    frozenSnapshots[windowId]
  }

  Set<Integer> allDelivered(int windowId) { receivedByWindow[windowId].toSet() }
}
