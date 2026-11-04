from __future__ import annotations
import argparse,csv,json,math,random,statistics
from collections import defaultdict
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

MODES=('fixed','proposed'); COLORS={'fixed':'#0072B2','legacy':'#E69F00','proposed':'#009E73'}
def weight_name_from_manifest(manifest,path):
    return manifest.get('weight_name') or Path(path).parent.name
def candidate_meets_guardrails(candidate,fixed):
    for depth in {r['depth_case'] for r in fixed}:
        c=[r for r in candidate if r['depth_case']==depth]; f=[r for r in fixed if r['depth_case']==depth]
        if not c or not f:return False
        if statistics.mean(r['pdr_pct'] for r in c) < statistics.mean(r['pdr_pct'] for r in f)-2:return False
        if statistics.mean(r['median_rtt_ms'] for r in c) > statistics.mean(r['median_rtt_ms'] for r in f)*1.05:return False
    return True
def _read(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def summarize_run(path):
    path=Path(path);m=json.loads((path/'manifest.json').read_text()); events=[]
    for f in sorted(path.glob('events-node-*.csv')): events += _read(f)
    sender=[r for r in events if r['node']=='1'];start=60000;cutoff=start+float(m['measurement_s'])*1000
    sends=[r for r in sender if r['event']=='SEND' and start<=float(r['time_ms'])<cutoff]
    attempt=lambda r:int(r.get('attempt') or 1)
    originals=[r for r in sends if attempt(r)==1]
    sent={int(r['seq']) for r in originals}
    attempts=[r for r in sends if int(r['seq']) in sent]
    retries=[r for r in attempts if attempt(r)>1]
    delivered={int(r['seq']) for r in events if r['event'] in ('DELIVER','LATE_DATA') and int(r['seq']) in sent}
    expected={(int(r['seq']),attempt(r)) for r in attempts if (r.get('ack_requested') or 'true').lower()=='true'}
    acked={(int(r['seq']),attempt(r)) for r in sender if r['event'] in ('ACK','LATE_ACK')}
    timeouts={(int(r['seq']),attempt(r)) for r in sender if r['event']=='TIMEOUT'}
    rtts=[float(r['rtt_ms']) for r in sender if r['event'] in ('ACK','LATE_ACK') and r['rtt_ms']]
    intervals=[float(r['interval_ms']) for r in originals]
    control_bytes=sum(int(r['payload_bytes'] or 0) for r in events if r['event'] in ('ACK_TX','REPORT_TX','REPORT_REQ'))
    windows=[r for r in sender if r['event']=='WINDOW'];unresolved=sum('resolved=false' in r['status'] for r in windows)
    precutoff=sum('control_applied=true' in r['status'] for r in windows)
    n=len(sent); dur=float(m['measurement_s'])
    return dict(run_dir=str(path),protocol_version=str(m.get('protocol_version','1')),mode=m['mode'],scenario=m['scenario'],depth_case=m['depth_case'],depth_m=int(m['depth_m']),seed=int(m['seed']),controller_id=m.get('controller_id',weight_name_from_manifest(m,path)),fixed_interval_ms=int(m.get('fixed_interval_ms',3000)),weights=';'.join(map(str,m['weights'])),weight_name=weight_name_from_manifest(m,path),
      unique_messages_generated=n,transmission_attempts=len(attempts),retry_attempts=len(retries),unique_messages_delivered=len(delivered),
      retry_overhead_pct=100*len(retries)/len(attempts) if attempts else 0,
      packets_transmitted=n,packets_received=len(delivered),pdr_pct=100*len(delivered)/n if n else 0,packet_loss_pct=100*(n-len(delivered))/n if n else 0,
      ack_ratio_pct=100*len(acked & expected)/len(expected) if expected else 0,average_rtt_ms=statistics.mean(rtts) if rtts else math.nan,median_rtt_ms=statistics.median(rtts) if rtts else math.nan,
      timeout_ratio_pct=100*len(timeouts & expected)/len(expected) if expected else 0,throughput_bps=len(delivered)*64*8/dur,average_interval_ms=statistics.mean(intervals) if intervals else math.nan,
      control_bytes=control_bytes,unresolved_rate=unresolved/len(windows) if windows else 0,precutoff_decisions=precutoff)

def validate_run_set(rows):
    versions={str(r['protocol_version']) for r in rows}
    if len(versions)>1:raise ValueError(f'mixed protocol versions: {sorted(versions)}')
    seen=set()
    for r in rows:
        key=(r['scenario'],r['depth_case'],int(r['seed']),r['mode'],r['controller_id'],int(r['fixed_interval_ms']))
        if key in seen:raise ValueError(f'duplicate experimental unit: {key}')
        seen.add(key)
    return True
def ci95(values):
    if len(values)<2:return (values[0],values[0]) if values else (math.nan,math.nan)
    rng=random.Random(20261024);means=[statistics.mean(rng.choices(values,k=len(values))) for _ in range(5000)];means.sort();return means[125],means[4874]
def write_csv(path,rows,fields=None):
    path.parent.mkdir(parents=True,exist_ok=True);fields=fields or list(rows[0])
    with path.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def aggregate(rows):
    groups=defaultdict(list)
    for r in rows:groups[(r['depth_case'],r['mode'])].append(r)
    out=[]
    metrics=['unique_messages_generated','transmission_attempts','retry_attempts','unique_messages_delivered','retry_overhead_pct','packets_transmitted','packets_received','pdr_pct','packet_loss_pct','ack_ratio_pct','average_rtt_ms','timeout_ratio_pct','throughput_bps','average_interval_ms']
    for depth in ('depth15','depth1000'):
      for mode in MODES:
       rs=groups.get((depth,mode),[])
       if rs:out.append({'depth_case':depth,'approach':mode,'runs':len(rs),**{k:statistics.mean(x[k] for x in rs) for k in metrics}})
    return out
def compute_paired_effects(rows):
    index={(r['depth_case'],r['seed'],r['mode']):r for r in rows};out=[]
    for depth in sorted({r['depth_case'] for r in rows}):
      for baseline in ('fixed','legacy'):
       pairs=[]
       for seed in sorted({r['seed'] for r in rows if r['depth_case']==depth}):
        p=index.get((depth,seed,'proposed'));b=index.get((depth,seed,baseline))
        if p and b:pairs.append((p,b))
       if not pairs:continue
       changes=[100*(p['throughput_bps']-b['throughput_bps'])/b['throughput_bps'] for p,b in pairs if b['throughput_bps']]
       lo,hi=ci95(changes)
       pdr_changes=[p['pdr_pct']-b['pdr_pct'] for p,b in pairs]
       pdr_lo,pdr_hi=ci95(pdr_changes)
       out.append(dict(depth_case=depth,baseline=baseline,paired_seeds=len(pairs),throughput_change_pct=statistics.mean(changes),throughput_ci95_low=lo,throughput_ci95_high=hi,
         pdr_change_pp=statistics.mean(pdr_changes),pdr_ci95_low=pdr_lo,pdr_ci95_high=pdr_hi,
         average_rtt_change_pct=statistics.mean(100*(p['average_rtt_ms']-b['average_rtt_ms'])/b['average_rtt_ms'] for p,b in pairs if b['average_rtt_ms']),
         median_rtt_change_pct=statistics.mean(100*(p['median_rtt_ms']-b['median_rtt_ms'])/b['median_rtt_ms'] for p,b in pairs if b['median_rtt_ms']),
         timeout_change_pp=statistics.mean(p['timeout_ratio_pct']-b['timeout_ratio_pct'] for p,b in pairs)))
    return out

def compute_depth_effects(rows):
    index={(r['mode'],int(r['seed']),r['depth_case']):r for r in rows};out=[]
    for mode in sorted({r['mode'] for r in rows}):
      differences=[]
      for seed in sorted({int(r['seed']) for r in rows if r['mode']==mode}):
        shallow=index.get((mode,seed,'depth15'));deep=index.get((mode,seed,'depth1000'))
        if shallow and deep:differences.append(deep['throughput_bps']-shallow['throughput_bps'])
      if not differences:continue
      lo,hi=ci95(differences)
      verdict='positive' if lo>0 else ('negative' if hi<0 else 'inconclusive')
      out.append(dict(mode=mode,paired_seeds=len(differences),throughput_change_bps=statistics.mean(differences),throughput_ci95_low=lo,throughput_ci95_high=hi,verdict=verdict))
    return out

def evaluate_success(effects,decision_counts):
    fixed={r['depth_case']:r for r in effects if r['baseline']=='fixed'}
    gates={}
    targets={'depth15':5.0,'depth1000':5.0}
    for depth,target in targets.items():
        row=fixed.get(depth)
        counts=decision_counts.get(depth,[])
        gates[depth]={
          'goodput_point':bool(row and row['throughput_change_pct']>=target),
          'goodput_ci':bool(row and row['throughput_ci95_low']>0),
          'pdr_point':bool(row and row['pdr_change_pp']>=5.0),
          'pdr_ci':bool(row and row['pdr_ci95_low']>0),
        }
    return {'success':all(all(values.values()) for values in gates.values()),'gates':gates,
            'targets_pct':targets}
def _bar(rows,metric,label,path,raw=None):
    fig,axes=plt.subplots(1,2,figsize=(8,3.6),layout='constrained')
    for ax,depth in zip(axes,('depth15','depth1000')):
      vals=[next(r[metric] for r in rows if r['depth_case']==depth and r['approach']==m) for m in MODES]
      cis=[ci95([r[metric] for r in raw if r['depth_case']==depth and r['mode']==m]) if raw else (v,v) for m,v in zip(MODES,vals)]
      errors=[[v-lo for v,(lo,hi) in zip(vals,cis)],[hi-v for v,(lo,hi) in zip(vals,cis)]]
      ax.bar(MODES,vals,yerr=errors,capsize=4,color=[COLORS[m] for m in MODES],edgecolor='black',hatch=[{'fixed':'//','proposed':'xx'}[m] for m in MODES]);ax.set_title(depth.replace('depth','Depth ')+' m');ax.set_ylabel(label);ax.set_ylim(bottom=0);ax.grid(axis='y',alpha=.25)
    fig.savefig(path.with_suffix('.png'),dpi=300);fig.savefig(path.with_suffix('.pdf'));plt.close(fig)
def window_rows(run):
    rows=[]
    for r in _read(Path(run)/'events-node-1.csv'):
      if r['event']!='WINDOW':continue
      if 'resolved=false' in r['status'] or not r['rtt_ms'] or not r['score']:continue
      detail=dict(x.split('=',1) for x in r['status'].split(';'))
      rows.append(dict(window=int(r['window_id']),average_rtt_ms=float(r['rtt_ms']),packet_loss_ratio=float(detail['loss']),ack_ratio=float(detail['ack']),timeout_ratio=float(detail['timeout']),weighted_score=float(r['score']),decision=r['action'],next_interval_ms=float(r['interval_ms'])))
    return rows
def time_binned_goodput(run,bin_seconds=30):
    manifest=json.loads((Path(run)/'manifest.json').read_text());bins=int(math.ceil(manifest['measurement_s']/bin_seconds));seen=[set() for _ in range(bins)]
    for f in Path(run).glob('events-node-[23].csv'):
      for r in _read(f):
       if r['event'] in ('DELIVER','LATE_DATA'):
        i=int((float(r['time_ms'])-60000)/(bin_seconds*1000))
        if 0<=i<bins:seen[i].add(int(r['seq']))
    return [((i+.5)*bin_seconds,len(seen[i])*64*8/bin_seconds) for i in range(bins)]
def analyze(root,out):
    paths=[p.parent for p in Path(root).rglob('manifest.json') if json.loads(p.read_text()).get('status')=='complete']
    rows=[summarize_run(p) for p in paths];validate_run_set(rows);out=Path(out);(out/'summary').mkdir(parents=True,exist_ok=True);(out/'figures').mkdir(parents=True,exist_ok=True)
    write_csv(out/'summary'/'run_summary.csv',rows);evaluation=[r for r in rows if 'evaluation' in Path(r['run_dir']).parts];overall=aggregate(evaluation);write_csv(out/'summary'/'overall_comparison.csv',overall);effects=compute_paired_effects(evaluation);write_csv(out/'summary'/'paired_effects.csv',effects);depth_effects=compute_depth_effects(evaluation)
    if depth_effects:write_csv(out/'summary'/'depth_effects.csv',depth_effects)
    if evaluation:
      decisions={depth:[r['precutoff_decisions'] for r in evaluation if r['depth_case']==depth and r['mode']=='proposed'] for depth in ('depth15','depth1000')}
      (out/'summary'/'success.json').write_text(json.dumps(evaluate_success(effects,decisions),indent=2),encoding='utf-8')
    for metric,label,name in [('throughput_bps','Throughput (bits/s)','throughput_comparison'),('pdr_pct','Packet delivery ratio (%)','packet_delivery'),('packet_loss_pct','Packet loss ratio (%)','packet_loss'),('average_rtt_ms','Average RTT (ms)','average_rtt'),('timeout_ratio_pct','Timeout ratio (%)','timeout_ratio')]:_bar(overall,metric,label,out/'figures'/name,evaluation)
    for depth in ('depth15','depth1000'):
      candidates=[r for r in rows if r['mode']=='proposed' and r['depth_case']==depth and 'evaluation' in Path(r['run_dir']).parts]
      if candidates:
       wr=[]
       for candidate in sorted(candidates,key=lambda x:x['seed']):
        for row in window_rows(candidate['run_dir']):
         row['source_seed']=candidate['seed'];row['source_run']=candidate['run_dir'];wr.append(row)
         if len(wr)>=3:break
        if len(wr)>=3:break
       if not wr:continue
       for i,row in enumerate(wr,1):row['observation']=i
       write_csv(out/'summary'/f'proposed_windows_{depth}.csv',wr)
       fig,ax=plt.subplots(figsize=(6,3.5),layout='constrained');ax.plot([x['observation'] for x in wr],[x['next_interval_ms'] for x in wr],marker='o',color=COLORS['proposed']);ax.set(xlabel='Resolved-window observation',ylabel='Next transmission interval (ms)',ylim=(1000,10000),xticks=[x['observation'] for x in wr]);ax.grid(alpha=.25);fig.savefig(out/'figures'/f'interval_{depth}.png',dpi=300);fig.savefig(out/'figures'/f'interval_{depth}.pdf');plt.close(fig)
       fig,ax=plt.subplots(figsize=(6,3.5),layout='constrained');ax.plot([x['observation'] for x in wr],[x['weighted_score'] for x in wr],marker='o',color=COLORS['proposed']);ax.axhline(.15,ls='--',color='#0072B2');ax.axhline(.30,ls='--',color='#D55E00');ax.set(xlabel='Resolved-window observation',ylabel='Weighted score',ylim=(0,1),xticks=[x['observation'] for x in wr]);ax.grid(alpha=.25);fig.savefig(out/'figures'/f'weighted_score_{depth}.png',dpi=300);fig.savefig(out/'figures'/f'weighted_score_{depth}.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(8,3.6),layout='constrained')
    for ax,depth in zip(axes,('depth15','depth1000')):
      for mode in MODES:
       rs=[r for r in evaluation if r['depth_case']==depth and r['mode']==mode]
       ax.scatter([r['average_rtt_ms'] for r in rs],[r['throughput_bps'] for r in rs],label=mode,color=COLORS[mode],marker={'fixed':'o','legacy':'s','proposed':'^'}[mode],alpha=.75)
      ax.set(title=depth.replace('depth','Depth ')+' m',xlabel='Average RTT (ms)',ylabel='Throughput (bits/s)');ax.grid(alpha=.25)
    axes[0].legend();fig.savefig(out/'figures'/'throughput_vs_rtt.png',dpi=300);fig.savefig(out/'figures'/'throughput_vs_rtt.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(8,3.6),layout='constrained')
    for ax,depth in zip(axes,('depth15','depth1000')):
      for mode in MODES:
       candidates=sorted([r for r in evaluation if r['depth_case']==depth and r['mode']==mode],key=lambda r:r['seed'])
       if candidates:
        points=time_binned_goodput(candidates[0]['run_dir']);ax.plot([p[0] for p in points],[p[1] for p in points],label=mode,color=COLORS[mode],marker={'fixed':'o','legacy':'s','proposed':'^'}[mode])
      ax.set(title=depth.replace('depth','Depth ')+' m (seed 11)',xlabel='Measurement time (s)',ylabel='Throughput (bits/s)');ax.grid(alpha=.25)
    axes[0].legend();fig.savefig(out/'figures'/'throughput_vs_time.png',dpi=300);fig.savefig(out/'figures'/'throughput_vs_time.pdf');plt.close(fig)
    return rows,overall
def select_calibration(root,out_file):
    rows=[summarize_run(p.parent) for p in Path(root).rglob('manifest.json') if 'calibration' in p.parts]
    fixed=[r for r in rows if r['mode']=='fixed'];by=defaultdict(list)
    for r in rows:
      if r['mode']=='proposed':by[r['weight_name']].append(r)
    valid=[]
    for name,rs in by.items():
      if len(rs)!=20: continue
      guard=candidate_meets_guardrails(rs,fixed)
      if guard:valid.append((statistics.mean(r['throughput_bps'] for r in rs),name,rs[0]['weights']))
    if not valid: valid=[(statistics.mean(r['throughput_bps'] for r in rs),name,rs[0]['weights']) for name,rs in by.items() if len(rs)==20]
    _,name,w=max(valid);data={'weight_name':name,'weights':[float(x) for x in w.split(';')],'selection':'maximum calibration mean goodput subject to per-depth aggregate PDR and median-RTT guardrails','calibration_seeds':list(range(1,11))}
    Path(out_file).parent.mkdir(parents=True,exist_ok=True);Path(out_file).write_text(json.dumps(data,indent=2));return data
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--runs',type=Path,default=Path('results/runs'));ap.add_argument('--output',type=Path,default=Path('results'));ap.add_argument('--select-calibration',type=Path);a=ap.parse_args()
    if a.select_calibration:print(json.dumps(select_calibration(a.runs,a.select_calibration),indent=2))
    else:analyze(a.runs,a.output)
if __name__=='__main__':main()
