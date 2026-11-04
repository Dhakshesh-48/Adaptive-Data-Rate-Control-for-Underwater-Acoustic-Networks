import org.arl.fjage.*
import org.arl.unet.*
import org.arl.unet.nodeinfo.NodeInfoParam

class AdaptiveExperimentAgent extends UnetAgent {
  def config
  def experimentState = new ExperimentState()
  def feedbackState = new ReceiverFeedbackState()
  def controller
  def retryScheduler
  AgentID transport
  int addr, seq=0, intervalMs=3000, timeoutCount=0
  long measurementStart, measurementEnd
  boolean cutoffReached=false

  AdaptiveExperimentAgent(config) {
    this.config=config
    controller=new AdaptiveRateController(config)
    retryScheduler=new RetryScheduler(config.retryEveryNew,config.maxRetriesPerWindow)
    intervalMs=config.initialIntervalMs
  }
  @Override void startup() {
    transport=agentForService(Services.TRANSPORT); subscribe topic(Topics.DATAGRAM)
    add new OneShotBehavior({
      addr=(int)get(agentForService(Services.NODE_INFO),NodeInfoParam.address); initializeLog()
      if(addr==1)add new WakerBehavior(60000,{measurementStart=currentTimeMillis();measurementEnd=measurementStart+config.measurementSeconds*1000L;sendOpportunity()})
    })
  }
  void sendOpportunity() {
    if(addr!=1)return
    if(currentTimeMillis()>=measurementEnd){onMeasurementCutoff();return}
    int proposedInterval=config.mode=='fixed'?config.fixedIntervalMs:intervalMs
    int usedInterval=retryScheduler.intervalForOpportunity(proposedInterval)
    def retry=config.mode=='proposed'?retryScheduler.takeRetry(true):null
    if(retry)sendRetry(retry)
    else sendOriginal(usedInterval)
    add new WakerBehavior(usedInterval,{sendOpportunity()})
  }
  void sendOriginal(int usedInterval) {
    seq++;int wid=((seq-1).intdiv(config.windowSize))+1;int dst=(seq%2==0?2:3);long now=currentTimeMillis()
    int position=((seq-1)%config.windowSize)+1
    boolean ackRequested=retryScheduler.ackRequested(config.mode,position,config.windowSize,1)
    experimentState.recordOriginal(seq,wid,dst,usedInterval)
    experimentState.recordAttempt(seq,1,now,ackRequested,ackRequested?now+config.ackTimeoutMs:0L)
    transmit(dst,ProtocolCodec.data(wid,seq,1,ackRequested))
    logEvent('SEND',seq,wid,dst,null,null,null,null,null,null,null,64,'DATA',1,ackRequested)
    if(ackRequested){int sentSeq=seq;add new WakerBehavior(config.ackTimeoutMs,{onTimeout(sentSeq,1)})}
    retryScheduler.noteOriginal(position,config.windowSize,usedInterval)
    if(seq%config.windowSize==0)closeWindow(wid,false)
  }
  void sendRetry(Map retry) {
    long now=currentTimeMillis();int packetSeq=retry.seq as int;int attempt=retry.attempt as int
    experimentState.recordAttempt(packetSeq,attempt,now,true,now+config.ackTimeoutMs)
    transmit(retry.destination as int,ProtocolCodec.data(retry.windowId as int,packetSeq,attempt,true))
    logEvent('SEND',packetSeq,retry.windowId as int,retry.destination as int,null,null,null,null,null,null,null,64,'RETRY',attempt,true)
    add new WakerBehavior(config.ackTimeoutMs,{onTimeout(packetSeq,attempt)})
  }
  void onTimeout(int packetSeq,int attempt=1) {
    def e=experimentState.recordTimeout(packetSeq,attempt);if(e.status!='TIMEOUT')return
    timeoutCount++;if(config.mode=='legacy'&&attempt==1)intervalMs=clamp(Math.round(intervalMs*1.5d)as int)
    def p=experimentState.packets[packetSeq];logEvent('TIMEOUT',packetSeq,p.windowId,p.destination,null,null,null,null,null,null,null,0,e.status,attempt,true)
    processCommitted()
  }
  void onMeasurementCutoff(){
    if(cutoffReached)return
    cutoffReached=true
    if(seq==0)return
    int wid=((seq-1).intdiv(config.windowSize))+1
    if(!experimentState.windows[wid].closed)experimentState.closeWindow(wid)
    add new WakerBehavior(config.finalFeedbackWaitMs,{startFallback(wid)})
  }
  void closeWindow(int wid,boolean finalWindow){
    if(!experimentState.windows[wid].closed)experimentState.closeWindow(wid)
    add new WakerBehavior(finalWindow?config.finalFeedbackWaitMs:config.feedbackWaitMs,{startFallback(wid)})
  }
  void startFallback(int wid){
    def w=experimentState.windows[wid]
    if(!w||w.committed||w.terminal!=null||w.receivers.every{w.reports.containsKey(it)}){processCommitted();return}
    boolean sent=requestMissingReports(wid,1)
    if(sent)add new WakerBehavior(config.feedbackRetryMs,{retryMissingReports(wid)})
  }
  void requestReport(int wid,int receiver){int attempt=experimentState.markReportAttempt(wid,receiver);String q=ProtocolCodec.reportRequest(wid);transmit(receiver,q);logEvent('REPORT_REQ',0,wid,receiver,null,null,null,null,null,null,null,q.bytes.length,"attempt-${attempt}")}
  boolean requestMissingReports(int wid,int limit){
    def w=experimentState.windows[wid];if(!w||w.committed||w.terminal!=null)return false
    def missing=w.receivers.findAll{!w.reports.containsKey(it)&&(w.attempts[it]?:0)<limit}
    missing.each{requestReport(wid,it as int)}
    !missing.isEmpty()
  }
  void retryMissingReports(int wid){
    def w=experimentState.windows[wid];if(!w||w.committed||w.terminal!=null)return
    requestMissingReports(wid,2)
    add new WakerBehavior(config.feedbackTerminalMs,{terminalizeMissing(wid)})
  }
  void terminalizeMissing(int wid){
    def w=experimentState.windows[wid];if(!w||w.committed||w.terminal!=null)return
    if(!w.receivers.every{w.reports.containsKey(it)})experimentState.markUnresolved(wid,'feedback-timeout')
    processCommitted()
  }
  @Override void processMessage(Message msg) {
    if(!(msg instanceof DatagramNtf)||msg.protocol!=Protocol.USER)return
    def p=ProtocolCodec.parse(new String(msg.data,'UTF-8'))
    if(p.type=='MALFORMED'){logEvent('MALFORMED',0,0,msg.from as int,null,null,null,null,null,null,null,msg.data.length,'ignored');return}
    if(p.type=='DATA'&&addr in [2,3]){
      def received=feedbackState.recordData(p.windowId as int,p.seq as int)
      logEvent(received.status,p.seq,p.windowId,msg.from as int,null,null,null,null,null,null,null,64,received.fresh?'unique':'duplicate-or-late',p.attempt,p.ackRequested)
      if(p.ackRequested){
        def snapshot=p.attempt==1?feedbackState.ackSnapshot(p.windowId as int):[snapshotWindow:null,delivered:[]]
        String ack=ProtocolCodec.ack(p.seq as int,p.windowId as int,p.attempt as int,addr,snapshot.snapshotWindow as Integer,snapshot.delivered as Collection<Integer>)
        transmit(msg.from as int,ack);logEvent('ACK_TX',p.seq,p.windowId,msg.from as int,null,null,null,null,null,null,null,ack.bytes.length,snapshot.snapshotWindow==null?'no-snapshot':"snapshot-${snapshot.snapshotWindow}",p.attempt,true)
      }
      return
    }
    if(p.type=='REPORT_REQ'&&addr in [2,3]){
      String report=ProtocolCodec.report(p.windowId as int,addr,feedbackState.snapshotForReport(p.windowId as int))
      transmit(msg.from as int,report);logEvent('REPORT_TX',0,p.windowId,msg.from as int,null,null,null,null,null,null,null,report.bytes.length,'sent');return
    }
    if(addr!=1)return
    if(p.type=='ACK')handleAck(p,msg.from as int)
    if(p.type=='REPORT')handleReport(p,msg.from as int)
  }
  void handleAck(Map p,int source){
    int packetSeq=p.seq as int
    def packet=experimentState.packets[packetSeq]
    def attempt=packet?.attempts[p.attempt as int]
    if(p.receiver!=source||!packet||!attempt||packet.destination!=source||packet.windowId!=p.windowId){logEvent('INVALID_ACK',packetSeq,p.windowId as int,source,null,null,null,null,null,null,null,0,'identity-mismatch',p.attempt,true);return}
    def e=experimentState.recordAck(packetSeq,p.attempt as int,currentTimeMillis())
    if(!(e.status in ['ACK','LATE_ACK'])){logEvent(e.status,packetSeq,0,0,e.rttMs,null,null,null,null,null,null,0,e.status,p.attempt,true);return}
    if(config.mode=='legacy'&&p.attempt==1){double ratio=seq?timeoutCount/(double)seq:0d;intervalMs=clamp(Math.round(intervalMs*(e.rttMs>3500||ratio>0.10?1.25d:0.90d))as int)}
    logEvent(e.status,packetSeq,packet.windowId,packet.destination,e.rttMs,null,null,null,null,null,null,0,e.status,p.attempt,true)
    if(p.snapshotWindow!=null){def snapshot=experimentState.recordSnapshot(p.snapshotWindow as int,source,p.delivered as Collection<Integer>);logEvent(snapshot.status,0,p.snapshotWindow as int,source,null,null,null,null,null,null,null,0,'piggyback');queueMissing(snapshot,source)}
    processCommitted()
  }
  void handleReport(Map p,int source){
    if(p.receiver!=source){logEvent('INVALID_REPORT',0,p.windowId as int,source,null,null,null,null,null,null,null,0,'identity-mismatch');return}
    def e=experimentState.recordSnapshot(p.windowId as int,source,p.delivered as Collection<Integer>);logEvent(e.status,0,p.windowId,source,null,null,null,null,null,null,null,0,'direct');queueMissing(e,source)
    processCommitted()
  }
  void queueMissing(Map snapshot,int source){
    if(config.mode!='proposed'||cutoffReached||currentTimeMillis()>=measurementEnd||snapshot.status!='SNAPSHOT')return
    retryScheduler.enqueue(snapshot.windowId as int,source,snapshot.missing as Collection<Integer>)
  }
  void processCommitted(){
    boolean controlAllowed=!cutoffReached&&currentTimeMillis()<measurementEnd
    experimentState.commitTerminalWindows(currentTimeMillis(),controlAllowed).each{m->
      def d
      if(config.mode=='proposed'&&m.resolved&&m.controlApplied)d=controller.observe(m)
      else if(config.mode=='proposed'&&!m.resolved)d=controller.observeUnresolved()
      else d=[resolved:m.resolved,score:null,action:m.resolved?'none':'unresolved',intervalMs:intervalMs,penalties:[:],phase:'none',epochGoodputBps:null]
      if(config.mode=='proposed'&&m.resolved&&m.controlApplied)intervalMs=d.intervalMs
      def penalties=d.penalties?:[:]
      String detail=m.resolved?"resolved=true;sent=${m.sent};delivered=${m.delivered};pdr=${m.pdr};ack=${m.ackRatio};loss=${m.lossRatio};timeout=${m.timeoutRatio};control_applied=${m.controlApplied};phase=${d.phase};epoch_goodput_bps=${d.epochGoodputBps}":"resolved=false;reason=${m.reason};control_applied=false"
      logEvent('WINDOW',0,m.windowId as int,0,m.resolved?m.meanRttMs:null,d.score,penalties.rtt,penalties.loss,penalties.ackFailure,penalties.timeout,d.action,0,detail)
    }
  }
  void transmit(int dst,String payload){send new DatagramReq(recipient:transport,to:dst,protocol:Protocol.USER,data:payload.bytes)}
  int clamp(int v){Math.max(config.minIntervalMs,Math.min(config.maxIntervalMs,v))}
  void initializeLog(){File f=logFile();f.parentFile.mkdirs();if(f.exists())throw new IllegalStateException("Refusing to append ${f}");f.text='event,node,mode,scenario,depth_case,seed,seq,window_id,peer,time_ms,rtt_ms,interval_ms,score,pr,pl,pa,pt,action,payload_bytes,status,attempt,ack_requested\n'}
  File logFile(){new File(config.outputDir,"events-node-${addr}.csv")}
  void logEvent(String event,int packetSeq,int wid,int peer,def rtt,def score,def pr,def pl,def pa,def pt,def action,int bytes,String status,def attempt=null,def ackRequested=null){def vals=[event,addr,config.mode,config.scenario,config.depthCase,config.seed,packetSeq,wid,peer,currentTimeMillis(),rtt,intervalMs,score,pr,pl,pa,pt,action,bytes,status,attempt,ackRequested];logFile().append(vals.collect{it==null?'':it.toString().replace(',',';')}.join(',')+'\n')}
}
