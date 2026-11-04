def loader = new GroovyClassLoader(this.class.classLoader)
def stateClass = loader.parseClass(new File('classes/ExperimentState.groovy'))
def s = stateClass.newInstance()
s.recordOriginal(1, 1, 2, 3000)
s.recordOriginal(2, 1, 3, 3000)
s.recordAttempt(1, 1, 1000L, true, 13000L)
s.recordAttempt(2, 1, 2000L, false, 0L)
assert s.recordTimeout(2, 1).status == 'NO_ACK_EXPECTED'
assert s.recordTimeout(1, 1).status == 'TIMEOUT'
assert s.recordTimeout(1, 1).status == 'DUPLICATE_TIMEOUT'
def late = s.recordAck(1, 1, 5000L)
assert late.status == 'LATE_ACK' && late.rttMs == 4000L
assert s.recordAck(1, 1, 6000L).status == 'DUPLICATE_ACK'
assert s.recordAck(99, 1, 6000L).status == 'UNKNOWN_ACK'
assert s.recordAck(2, 9, 6000L).status == 'UNKNOWN_ATTEMPT_ACK'

// A retry is another attempt for the same useful message, never another original.
s.recordAttempt(2, 2, 6000L, true, 18000L)
assert s.recordAck(2, 2, 7000L).status == 'ACK'
boolean duplicateAttempt = false
try { s.recordAttempt(2, 2, 8000L, true, 20000L) } catch (IllegalArgumentException ignored) { duplicateAttempt = true }
assert duplicateAttempt

s.closeWindow(1)
s.markReportAttempt(1, 2)
s.markReportAttempt(1, 3)
def receiver2 = s.recordSnapshot(1, 2, [1])
assert receiver2.status == 'SNAPSHOT'
assert receiver2.expected == [1] as Set && receiver2.delivered == [1] as Set && receiver2.missing.isEmpty()
assert s.recordSnapshot(1, 2, []).status == 'DUPLICATE_SNAPSHOT'
assert s.recordSnapshot(1, 99, [1]).status == 'UNEXPECTED_SNAPSHOT'
def receiver3 = s.recordSnapshot(1, 3, [])
assert receiver3.status == 'SNAPSHOT'
assert receiver3.expected == [2] as Set && receiver3.delivered.isEmpty() && receiver3.missing == [2] as Set
def rows = s.commitTerminalWindows(14000L, true)
assert rows.size() == 1
assert rows[0].sent == 2 && rows[0].delivered == 1
assert rows[0].lossRatio == 0.5d && rows[0].ackRatio == 1d && rows[0].timeoutRatio == 1d
assert rows[0].meanRttMs == 4000d
assert rows[0].pdr == 0.5d && rows[0].sendDurationMs == 4000L && rows[0].controlApplied
assert rows[0].originalAttempts == 2 && rows[0].retryAttempts == 1
assert s.recordSnapshot(1, 2, [1]).status == 'LATE_SNAPSHOT'

// A later terminal window cannot pass an earlier open window.
def ordered = stateClass.newInstance()
ordered.recordOriginal(10, 1, 2, 3000); ordered.recordAttempt(10, 1, 0L, true, 30000L)
ordered.recordOriginal(20, 2, 2, 3000); ordered.recordAttempt(20, 1, 1000L, true, 31000L)
ordered.closeWindow(2)
ordered.recordAck(20, 1, 2000L)
ordered.recordSnapshot(2, 2, [20])
assert ordered.commitTerminalWindows(31000L, true).isEmpty()
ordered.closeWindow(1)
ordered.markUnresolved(1, 'feedback-timeout')
def committed = ordered.commitTerminalWindows(31000L, false)
assert committed*.windowId == [1, 2]
assert !committed[0].resolved && committed[0].reason == 'feedback-timeout'
assert committed[1].resolved && !committed[1].controlApplied

// No RTT sample is terminal but unresolved for control.
def noRtt = stateClass.newInstance()
noRtt.recordOriginal(30, 1, 2, 3000)
noRtt.recordAttempt(30, 1, 0L, true, 30000L)
noRtt.closeWindow(1)
noRtt.recordSnapshot(1, 2, [])
def missing = noRtt.commitTerminalWindows(30000L, true)
assert missing.size() == 1 && !missing[0].resolved && missing[0].reason == 'missing-rtt'
println 'STATE_TEST_PASS'
