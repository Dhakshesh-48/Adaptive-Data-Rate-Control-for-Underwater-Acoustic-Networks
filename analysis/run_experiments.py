from __future__ import annotations
import argparse, json, os, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL_VERSION='3'
RESULT_ROOT=ROOT/'results'/'v3'/'runs'
WEIGHTS=((0.10,0.60,0.15,0.15),(0.15,0.55,0.15,0.15),(0.20,0.50,0.15,0.15))
RETRY_EVERY_NEW=(2,3,4)
MAX_RETRIES_PER_WINDOW=(1,2,3)

def controller_candidates(reliability_floor=0.50):
    rows=[]
    for wi,weights in enumerate(WEIGHTS,1):
      for every in RETRY_EVERY_NEW:
       for cap in MAX_RETRIES_PER_WINDOW:
        cid=f'w{wi}-e{every}-c{cap}'
        rows.append(dict(controller_id=cid,weights=weights,rtt_reference_ms=10000,
          healthy_threshold=0.50,poor_threshold=0.70,
          reliability_floor=float(reliability_floor),probe_margin=0.01,
          retry_every_new=every,max_retries_per_window=cap,ack_policy='window-tail'))
    return rows

def _baseline(mode='fixed',fixed_interval_ms=3000):
    return dict(mode=mode,controller_id=mode,weights=WEIGHTS[0],rtt_reference_ms=10000,
      healthy_threshold=0.50,poor_threshold=0.70,reliability_floor=0.50,
      probe_margin=0.01,fixed_interval_ms=fixed_interval_ms,retry_every_new=3,
      max_retries_per_window=0,ack_policy='per-message')

def build_runs(kind,seeds=None,scenarios=None,frozen=None):
    defaults={'screening':range(181,186),'calibration':range(204,211) if frozen and frozen.get('advanced_candidates') else range(201,204),
              'evaluation':range(211,231)}
    if kind not in defaults:raise ValueError(f'unsupported phase: {kind}')
    seeds=list(seeds or defaults[kind])
    scenarios=list(scenarios or ['moderate'])
    rows=[]
    for scenario in scenarios:
      for depth in ('depth15','depth1000'):
       for seed in seeds:
        base=dict(scenario=scenario,depth_case=depth,seed=seed)
        if kind in ('screening','calibration'):
          rows.append(base|_baseline())
          floor=float((frozen or {}).get('reliability_floor',0.50))
          candidates=(frozen or {}).get('advanced_candidates') or controller_candidates(floor)
          rows.extend(base|{'mode':'proposed','fixed_interval_ms':3000}|candidate for candidate in candidates)
        else:
          if not frozen:raise ValueError('evaluation requires frozen controller configuration')
          chosen={k:frozen[k] for k in ('controller_id','weights','rtt_reference_ms','healthy_threshold','poor_threshold','reliability_floor','probe_margin','retry_every_new','max_retries_per_window')}
          chosen['ack_policy']='window-tail'
          rows += [base|_baseline('fixed'),base|{'mode':'proposed','fixed_interval_ms':3000}|chosen]
    return rows

def expected_manifest(row,measurement_s):
    return {'protocol_version':PROTOCOL_VERSION,'mode':row['mode'],'scenario':row['scenario'],
      'depth_case':row['depth_case'],'seed':int(row['seed']),'measurement_s':int(measurement_s),
      'controller_id':row['controller_id'],'fixed_interval_ms':int(row['fixed_interval_ms']),
      'weights':list(row['weights']),'rtt_reference_ms':float(row['rtt_reference_ms']),
      'healthy_threshold':float(row['healthy_threshold']),'poor_threshold':float(row['poor_threshold']),
      'reliability_floor':float(row['reliability_floor']),'probe_margin':float(row['probe_margin']),
      'retry_every_new':int(row['retry_every_new']),'max_retries_per_window':int(row['max_retries_per_window']),
      'ack_policy':row['ack_policy']}

def simulator_output_failed(stdout,stderr):
    output=f'{stdout}\n{stderr}'
    return 'SEVERE:' in output or 'Agent experiment died' in output

def validate_completed_run(path,expected):
    path=Path(path);manifest=path/'manifest.json'
    if not manifest.exists():raise RuntimeError(f'missing manifest: {path}')
    actual=json.loads(manifest.read_text(encoding='utf-8'))
    if actual.get('status')!='complete':raise RuntimeError(f'incomplete manifest: {path}')
    mismatches={k:(actual.get(k),v) for k,v in expected.items() if actual.get(k)!=v}
    if mismatches:raise RuntimeError(f'incompatible completed run {path}: {mismatches}')
    missing=[str(path/f'events-node-{node}.csv') for node in (1,2,3) if not (path/f'events-node-{node}.csv').is_file()]
    if missing:raise RuntimeError(f'missing event files: {missing}')
    stdout=(path/'stdout.txt').read_text(encoding='utf-8',errors='replace') if (path/'stdout.txt').exists() else ''
    stderr=(path/'stderr.txt').read_text(encoding='utf-8',errors='replace') if (path/'stderr.txt').exists() else ''
    if simulator_output_failed(stdout,stderr):raise RuntimeError(f'simulator reported an agent failure: {path}')
    return actual

def run_directory(row,phase,root=RESULT_ROOT):
    return Path(root)/phase/row['scenario']/row['depth_case']/row['mode']/row['controller_id']/f"seed-{row['seed']:03d}"

def prepare_run_directories(rows,phase,root=RESULT_ROOT):
    paths=[]
    for row in rows:
        path=run_directory(row,phase,root)
        path.mkdir(parents=True,exist_ok=True)
        paths.append(path)
    return paths

def run_one(row,phase,measurement_s=180,force=False,root=RESULT_ROOT):
    out=run_directory(row,phase,root)
    manifest=out/'manifest.json'
    expected=expected_manifest(row,measurement_s)
    if manifest.exists():
      try:
        validate_completed_run(out,expected)
        return str(out)
      except RuntimeError:
        if not force:raise
    if out.exists() and any(out.iterdir()):
      if not force:raise RuntimeError(f'incomplete nonempty run: {out}')
      shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy(); env.update({
      'ADR_MODE':row['mode'],'ADR_SCENARIO':row['scenario'],'ADR_DEPTH_CASE':row['depth_case'],
      'ADR_SEED':str(row['seed']),'ADR_OUTPUT_DIR':str(out),'ADR_MEASUREMENT_S':str(measurement_s),
      'ADR_FIXED_INTERVAL_MS':str(row['fixed_interval_ms']),
      'ADR_WEIGHTS':','.join(map(str,row['weights'])),'ADR_RTT_REFERENCE_MS':str(row['rtt_reference_ms']),
      'ADR_HEALTHY_THRESHOLD':str(row['healthy_threshold']),'ADR_POOR_THRESHOLD':str(row['poor_threshold']),
      'ADR_RELIABILITY_FLOOR':str(row['reliability_floor']),'ADR_PROBE_MARGIN':str(row['probe_margin']),
      'ADR_RETRY_EVERY_NEW':str(row['retry_every_new']),'ADR_MAX_RETRIES_PER_WINDOW':str(row['max_retries_per_window'])})
    cmd=[str(ROOT/'bin'/'unet.bat'),str(ROOT/'simulations'/'experiment.groovy')]
    p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
    (out/'stdout.txt').write_text(p.stdout,encoding='utf-8');(out/'stderr.txt').write_text(p.stderr,encoding='utf-8')
    if p.returncode or simulator_output_failed(p.stdout,p.stderr) or not manifest.exists():raise RuntimeError(f'run failed: {out}; simulator rc={p.returncode}')
    data=json.loads(manifest.read_text(encoding='utf-8'));data.update(expected)
    manifest.write_text(json.dumps(data,indent=2),encoding='utf-8')
    validate_completed_run(out,expected)
    return str(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['screening','calibration','evaluation'])
    ap.add_argument('--config',type=Path);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--measurement',type=int,default=180);ap.add_argument('--force',action='store_true');ap.add_argument('--root',type=Path,default=RESULT_ROOT)
    a=ap.parse_args();kind=a.phase
    frozen=json.loads(a.config.read_text()) if a.config else None
    rows=build_runs(kind,scenarios=['moderate'],frozen=frozen)
    prepare_run_directories(rows,kind,a.root)
    failures=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
      futures={pool.submit(run_one,r,kind,a.measurement,a.force,a.root):r for r in rows}
      for f in as_completed(futures):
        try: print('COMPLETE',f.result(),flush=True)
        except Exception as e: failures.append((futures[f],str(e)));print('FAILED',e,flush=True)
    if failures: raise SystemExit(f'{len(failures)} runs failed')

if __name__=='__main__': main()
