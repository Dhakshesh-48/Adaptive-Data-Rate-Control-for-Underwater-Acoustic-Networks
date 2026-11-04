def loader = new GroovyClassLoader(this.class.classLoader)
def codec = loader.parseClass(new File('classes/ProtocolCodec.groovy'))
String original = codec.data(7, 42, 1, true)
assert original.bytes.length == 64
assert codec.parse(original) == [type:'DATA', windowId:7, seq:42, attempt:1, ackRequested:true]
String retry = codec.data(7, 42, 2, false)
assert retry.bytes.length == 64
assert codec.parse(retry) == [type:'DATA', windowId:7, seq:42, attempt:2, ackRequested:false]
assert codec.parse(codec.ack(42, 7, 1, 2, null, [])) == [
  type:'ACK', seq:42, windowId:7, attempt:1, receiver:2, snapshotWindow:null, delivered:[]]
assert codec.parse(codec.ack(52, 8, 2, 3, 7, [44,42])) == [
  type:'ACK', seq:52, windowId:8, attempt:2, receiver:3, snapshotWindow:7, delivered:[42,44]]
assert codec.parse(codec.reportRequest(7)) == [type:'REPORT_REQ', windowId:7]
assert codec.parse(codec.report(7, 3, [42,44])) == [type:'REPORT', windowId:7, receiver:3, delivered:[42,44]]
def immutableDelivered = Collections.unmodifiableList([44,42])
assert codec.parse(codec.report(7, 3, immutableDelivered)) == [type:'REPORT', windowId:7, receiver:3, delivered:[42,44]]
assert immutableDelivered == [44,42]
assert codec.parse('D:7:42:0:1'.padRight(64, 'x')) == [type:'MALFORMED']
assert codec.parse('D:7:42:1:maybe'.padRight(64, 'x')) == [type:'MALFORMED']
assert codec.parse('A:52:8:0:3:7:42') == [type:'MALFORMED']
assert codec.parse('A:52:8:2:3:7:not-an-int') == [type:'MALFORMED']
assert codec.parse('A:52:8:2:3:-:') == [type:'MALFORMED']
assert codec.parse('not-a-packet') == [type:'MALFORMED']
println 'PROTOCOL_TEST_PASS'
