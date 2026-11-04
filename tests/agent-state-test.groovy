def loader = new GroovyClassLoader(this.class.classLoader)
def feedbackClass = loader.parseClass(new File('classes/ReceiverFeedbackState.groovy'))
def state = feedbackClass.newInstance()

assert state.recordData(1, 1).fresh
assert state.recordData(1, 1).status == 'DUPLICATE_DATA'
assert state.ackSnapshot(1) == [snapshotWindow:null, delivered:[]]

// First DATA in N+1 freezes N; later N data remains visible offline but not in feedback.
assert state.recordData(2, 11).frozenWindow == 1
assert state.ackSnapshot(2) == [snapshotWindow:1, delivered:[1]]
assert state.recordData(1, 2).status == 'LATE_DATA'
assert state.ackSnapshot(2) == [snapshotWindow:1, delivered:[1]]
assert state.allDelivered(1) == [1,2] as Set

// Explicit fallback freezes a window even if the next window never arrives.
assert state.recordData(3, 21).fresh
assert state.snapshotForReport(3) == [21]
assert state.recordData(3, 22).status == 'LATE_DATA'
assert state.snapshotForReport(3) == [21]

println 'AGENT_STATE_TEST_PASS'
