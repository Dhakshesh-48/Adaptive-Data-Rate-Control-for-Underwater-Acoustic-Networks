class ProtocolCodec {
  static String data(int windowId, int seq, int attempt, boolean ackRequested) {
    "D:${windowId}:${seq}:${attempt}:${ackRequested ? 1 : 0}".padRight(64, 'x')
  }
  static String ack(int seq, int windowId, int attempt, int receiver, Integer snapshotWindow, Collection<Integer> delivered) {
    String snapshot = snapshotWindow == null ? '-' : snapshotWindow.toString()
    String sequences = snapshotWindow == null ? '-' : delivered.toSet().sort().join(',')
    "A:${seq}:${windowId}:${attempt}:${receiver}:${snapshot}:${sequences}"
  }
  static String reportRequest(int windowId) { "Q:${windowId}" }
  static String report(int windowId, int receiver, Collection<Integer> delivered) { "R:${windowId}:${receiver}:${delivered.toSet().sort().join(',')}" }
  static Map parse(String raw) {
    try {
      String s=raw.replaceAll('x+$','')
      def p=s.split(':',-1)
      if(p[0]=='D' && p.size()==5) {
        int windowId=p[1].toInteger(), seq=p[2].toInteger(), attempt=p[3].toInteger()
        if (windowId <= 0 || seq <= 0 || attempt <= 0 || !(p[4] in ['0','1'])) return [type:'MALFORMED']
        return [type:'DATA',windowId:windowId,seq:seq,attempt:attempt,ackRequested:p[4]=='1']
      }
      if(p[0]=='A' && p.size()==7) {
        int seq=p[1].toInteger(), windowId=p[2].toInteger(), attempt=p[3].toInteger(), receiver=p[4].toInteger()
        if (seq <= 0 || windowId <= 0 || attempt <= 0 || receiver <= 0) return [type:'MALFORMED']
        if (p[5]=='-' && p[6]=='-') return [type:'ACK',seq:seq,windowId:windowId,attempt:attempt,receiver:receiver,snapshotWindow:null,delivered:[]]
        if (p[5]=='-' || p[6]=='-') return [type:'MALFORMED']
        int snapshotWindow=p[5].toInteger()
        if (snapshotWindow <= 0 || snapshotWindow >= windowId) return [type:'MALFORMED']
        List<Integer> delivered=p[6] ? p[6].split(',').collect{it.toInteger()}.toSet().sort() : []
        return [type:'ACK',seq:seq,windowId:windowId,attempt:attempt,receiver:receiver,snapshotWindow:snapshotWindow,delivered:delivered]
      }
      if(p[0]=='Q' && p.size()==2) return [type:'REPORT_REQ',windowId:p[1].toInteger()]
      if(p[0]=='R' && p.size()==4) return [type:'REPORT',windowId:p[1].toInteger(),receiver:p[2].toInteger(),delivered:p[3] ? p[3].split(',').collect{it.toInteger()} : []]
    } catch(Exception ignored) {}
    [type:'MALFORMED']
  }
}
