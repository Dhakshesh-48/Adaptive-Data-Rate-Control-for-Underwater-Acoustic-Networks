class ExperimentState {
  Map<Integer,Map> packets = [:]
  Map<Integer,Map> windows = [:]
  int commitCursor = 1

  Map recordOriginal(int seq, int windowId, int destination, int intervalMs = 0) {
    if (packets.containsKey(seq)) throw new IllegalArgumentException('Duplicate sequence')
    packets[seq] = [seq:seq, windowId:windowId, destination:destination, delivered:null, attempts:[:]]
    def w = windows.computeIfAbsent(windowId) {
      [id:windowId, seqs:[], receivers:[] as Set, reports:[:], attempts:[:], closed:false,
       terminal:null, committed:false, reason:null, intervalMs:intervalMs]
    }
    if (w.intervalMs == 0) w.intervalMs = intervalMs
    if (intervalMs && w.intervalMs != intervalMs) throw new IllegalArgumentException('Interval changed within window')
    w.seqs << seq
    w.receivers << destination
    packets[seq]
  }

  Map recordAttempt(int seq, int attempt, long sentAt, boolean ackExpected, long ackDeadline) {
    def p = packets[seq]
    if (!p) throw new IllegalArgumentException('Unknown sequence')
    if (attempt <= 0) throw new IllegalArgumentException('Attempt must be positive')
    if (p.attempts.containsKey(attempt)) throw new IllegalArgumentException('Duplicate attempt')
    if (ackExpected && ackDeadline <= sentAt) throw new IllegalArgumentException('ACK deadline must follow send time')
    p.attempts[attempt] = [attempt:attempt, sentAt:sentAt, ackExpected:ackExpected,
      ackDeadline:ackDeadline, ackAt:null, rttMs:null, timedOut:false]
  }

  Map recordSend(int seq, int windowId, int destination, long sentAt, long ackDeadline, int intervalMs = 0) {
    recordOriginal(seq, windowId, destination, intervalMs)
    recordAttempt(seq, 1, sentAt, true, ackDeadline)
    packets[seq]
  }

  Map recordAck(int seq, int attempt, long ackAt) {
    def p=packets[seq]
    if (!p) return [status:'UNKNOWN_ACK', seq:seq, attempt:attempt]
    def a=p.attempts[attempt]
    if (!a) return [status:'UNKNOWN_ATTEMPT_ACK', seq:seq, attempt:attempt]
    if (!a.ackExpected) return [status:'UNEXPECTED_ACK', seq:seq, attempt:attempt]
    if (a.ackAt != null) return [status:'DUPLICATE_ACK', seq:seq, attempt:attempt, rttMs:a.rttMs]
    a.ackAt=ackAt
    a.rttMs=ackAt-a.sentAt
    [status:a.timedOut ? 'LATE_ACK':'ACK', seq:seq, attempt:attempt, rttMs:a.rttMs]
  }

  Map recordAck(int seq, long ackAt) { recordAck(seq, 1, ackAt) }

  Map recordTimeout(int seq, int attempt) {
    def p=packets[seq]
    if (!p) return [status:'UNKNOWN_TIMEOUT', seq:seq, attempt:attempt]
    def a=p.attempts[attempt]
    if (!a) return [status:'UNKNOWN_ATTEMPT_TIMEOUT', seq:seq, attempt:attempt]
    if (!a.ackExpected) return [status:'NO_ACK_EXPECTED', seq:seq, attempt:attempt]
    if (a.timedOut || a.ackAt != null) return [status:a.timedOut ? 'DUPLICATE_TIMEOUT':'ACKED_BEFORE_TIMEOUT', seq:seq, attempt:attempt]
    a.timedOut=true
    [status:'TIMEOUT', seq:seq, attempt:attempt]
  }

  Map recordTimeout(int seq) { recordTimeout(seq, 1) }

  void closeWindow(int windowId) { requireWindow(windowId).closed=true }

  int markReportAttempt(int windowId, int receiver) {
    def w=requireWindow(windowId)
    w.attempts[receiver]=(w.attempts[receiver] ?: 0)+1
    w.attempts[receiver]
  }

  Map recordSnapshot(int windowId, int receiver, Collection<Integer> deliveredSeqs) {
    def w=windows[windowId]
    if (!w) return [status:'UNKNOWN_SNAPSHOT', windowId:windowId, receiver:receiver]
    if (w.terminal != null || w.committed) return [status:'LATE_SNAPSHOT', windowId:windowId, receiver:receiver]
    if (!(receiver in w.receivers)) return [status:'UNEXPECTED_SNAPSHOT', windowId:windowId, receiver:receiver]
    if (w.reports.containsKey(receiver)) return [status:'DUPLICATE_SNAPSHOT', windowId:windowId, receiver:receiver]
    Set<Integer> expected=w.seqs.findAll { packets[it].destination == receiver } as Set<Integer>
    Set<Integer> delivered=(deliveredSeqs as Set<Integer>).intersect(expected) as Set<Integer>
    expected.each { packets[it].delivered = delivered.contains(it) }
    w.reports[receiver]=delivered.asImmutable()
    [status:'SNAPSHOT', windowId:windowId, receiver:receiver,
     expected:expected.asImmutable(), delivered:delivered.asImmutable(),
     missing:(expected-delivered).asImmutable()]
  }

  Map recordReport(int windowId, int receiver, Collection<Integer> deliveredSeqs) {
    recordSnapshot(windowId, receiver, deliveredSeqs)
  }

  Map markUnresolved(int windowId, String reason) {
    def w=requireWindow(windowId)
    if (w.terminal != null || w.committed) return [status:'ALREADY_TERMINAL', windowId:windowId]
    w.terminal='unresolved'
    w.reason=reason
    [status:'UNRESOLVED', windowId:windowId, reason:reason]
  }

  List<Map> commitTerminalWindows(long now, boolean controlAllowed) {
    List<Map> answer=[]
    while (windows.containsKey(commitCursor)) {
      def w=windows[commitCursor]
      if (!w.closed) break
      if (w.terminal == null) {
        boolean snapshotsReady=w.receivers.every { w.reports.containsKey(it) }
        boolean ackReady=w.seqs.every {
          def a=packets[it].attempts[1]
          a && (!a.ackExpected || a.ackAt != null || now >= a.ackDeadline)
        }
        if (!snapshotsReady || !ackReady) break
        def sampled=w.seqs.collect { packets[it].attempts[1] }.findAll { it?.ackExpected }
        def rtts=sampled.findAll { it.rttMs != null }.collect { it.rttMs as double }
        if (!rtts) {
          w.terminal='unresolved'
          w.reason='missing-rtt'
        } else {
          w.terminal='resolved'
        }
      }
      Map row = w.terminal == 'resolved' ? metrics(w, controlAllowed) : [
        windowId:w.id, resolved:false, reason:w.reason, controlApplied:false]
      w.committed=true
      answer << row.asImmutable()
      commitCursor++
    }
    answer
  }

  List<Map> finalizeReadyWindows() { commitTerminalWindows(Long.MAX_VALUE, true) }

  private Map metrics(Map w, boolean controlAllowed) {
    def ps=w.seqs.collect { packets[it] }
    def originals=ps.collect { it.attempts[1] }
    def sampled=originals.findAll { it.ackExpected }
    def rtts=sampled.findAll { it.rttMs != null }.collect { it.rttMs as double }
    long first=originals.collect { it.sentAt as long }.min()
    long last=originals.collect { it.sentAt as long }.max()
    int sent=ps.size()
    int delivered=ps.count { it.delivered == true }
    [windowId:w.id, resolved:true, sent:sent, delivered:delivered, pdr:delivered/(double)sent,
     lossRatio:(sent-delivered)/(double)sent, ackRatio:sampled.count { it.ackAt != null }/(double)sampled.size(),
     timeoutRatio:sampled.count { it.timedOut }/(double)sampled.size(), meanRttMs:rtts.sum()/rtts.size(),
     firstSendMs:first, lastSendMs:last, sendDurationMs:last-first+(w.intervalMs as int),
     intervalMs:w.intervalMs as int, controlApplied:controlAllowed,
     originalAttempts:originals.size(), retryAttempts:ps.sum { p -> p.attempts.keySet().count { it > 1 } }]
  }

  private Map requireWindow(int id) {
    if(!windows[id]) throw new IllegalArgumentException('Unknown window')
    windows[id]
  }
}
