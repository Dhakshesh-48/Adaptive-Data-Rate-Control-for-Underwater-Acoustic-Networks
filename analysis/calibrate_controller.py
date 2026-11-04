from __future__ import annotations
import argparse,csv,json,statistics
from collections import defaultdict
from pathlib import Path

DEPTHS=('depth15','depth1000')

def derive_reliability_floor(fixed_rows):
    means=[]
    for depth in DEPTHS:
        values=[float(r['pdr_pct']) for r in fixed_rows if r['depth_case']==depth]
        if not values:raise RuntimeError(f'missing fixed rows for {depth}')
        means.append(statistics.mean(values)/100.0-0.02)
    return max(0.0,min(means))

def screen_candidates(rows,candidate_order,count=6):
    fixed={(r['depth_case'],int(r['seed'])):r for r in rows if r['mode']=='fixed'}
    ranked=[]
    for order,cid in enumerate(candidate_order):
        candidates=[r for r in rows if r['mode']=='proposed' and r['controller_id']==cid]
        gains=[];pdr_changes=[];violation=0.0
        for depth in DEPTHS:
            pairs=[(r,fixed.get((depth,int(r['seed'])))) for r in candidates if r['depth_case']==depth]
            pairs=[p for p in pairs if p[1] is not None]
            if not pairs:
                violation=float('inf');break
            gain=statistics.mean(100*(float(p['throughput_bps'])-float(f['throughput_bps']))/float(f['throughput_bps']) for p,f in pairs)
            pdr=statistics.mean(float(p['pdr_pct'])-float(f['pdr_pct']) for p,f in pairs)
            gains.append(gain);pdr_changes.append(pdr)
            violation += max(0.0,5.0-gain)+max(0.0,5.0-pdr)
        retry_overhead=statistics.mean(float(r.get('retry_overhead_pct',0)) for r in candidates) if candidates else float('inf')
        overhead=statistics.mean(float(r.get('control_bytes',0)) for r in candidates) if candidates else float('inf')
        ranked.append((violation,-min(gains) if gains else float('inf'),-min(pdr_changes) if pdr_changes else float('inf'),retry_overhead,overhead,order,cid))
    return [row[-1] for row in sorted(ranked)[:count]]

def select_candidate(rows,candidate_order):
    fixed={(r['depth_case'],int(r['seed'])):r for r in rows if r['mode']=='fixed'}
    valid=[]
    for order,cid in enumerate(candidate_order):
        candidates=[r for r in rows if r['mode']=='proposed' and r['controller_id']==cid]
        depth_gains=[];pdr_changes=[]
        for depth in DEPTHS:
            pairs=[(r,fixed.get((depth,int(r['seed'])))) for r in candidates if r['depth_case']==depth]
            pairs=[p for p in pairs if p[1] is not None]
            if not pairs:break
            depth_gains.append(statistics.mean(100*(float(p['throughput_bps'])-float(f['throughput_bps']))/float(f['throughput_bps']) for p,f in pairs))
            pdr_changes.append(statistics.mean(float(p['pdr_pct'])-float(f['pdr_pct']) for p,f in pairs))
        if len(depth_gains)!=2 or min(depth_gains)<5.0 or min(pdr_changes)<5.0:continue
        retry_overhead=statistics.mean(float(r.get('retry_overhead_pct',0)) for r in candidates)
        overhead=statistics.mean(float(r.get('control_bytes',0)) for r in candidates)
        valid.append((min(depth_gains),min(pdr_changes),-retry_overhead,-overhead,-order,cid,depth_gains,pdr_changes))
    if not valid:raise RuntimeError('no calibration candidate satisfies +5% throughput and +5 PDR points at both depths')
    best=max(valid)
    return {'controller_id':best[5],'minimum_depth_gain_pct':best[0],'minimum_depth_pdr_gain_pp':best[1],
            'depth_gains_pct':dict(zip(DEPTHS,best[6])),'depth_pdr_gains_pp':dict(zip(DEPTHS,best[7])),
            'selection':'require both-depth +5% throughput and +5 PDR points; maximize minimum throughput gain; ties minimum PDR gain, retry overhead, control overhead, declaration order'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('summary_csv',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--candidate-order',type=Path,required=True);a=ap.parse_args()
    with a.summary_csv.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    order=json.loads(a.candidate_order.read_text(encoding='utf-8'))
    selected=select_candidate(rows,order)
    selected['reliability_floor']=derive_reliability_floor([r for r in rows if r['mode']=='fixed'])
    source=next(r for r in rows if r.get('controller_id')==selected['controller_id'])
    for key in ('weights','rtt_reference_ms','healthy_threshold','poor_threshold','probe_margin','retry_every_new','max_retries_per_window'):selected[key]=source[key]
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(selected,indent=2),encoding='utf-8')
    print(json.dumps(selected,indent=2))

if __name__=='__main__':main()
