import csv,json,tempfile,unittest
from pathlib import Path
from analysis.analyze_results import (summarize_run, weight_name_from_manifest,
    candidate_meets_guardrails, compute_paired_effects, compute_depth_effects, time_binned_goodput,
    validate_run_set, evaluate_success, window_rows, MODES)

class AnalysisTests(unittest.TestCase):
    def test_v3_official_comparison_excludes_legacy(self):
        self.assertEqual(('fixed','proposed'),MODES)

    def test_window_plot_rows_skip_unresolved_windows(self):
        Path('tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='tmp') as td:
            run=Path(td);fields='event,node,window_id,rtt_ms,score,action,interval_ms,status'.split(',')
            with (run/'events-node-1.csv').open('w',newline='',encoding='utf-8') as f:
                out=csv.DictWriter(f,fields);out.writeheader();out.writerows([
                  {'event':'WINDOW','node':'1','window_id':'1','rtt_ms':'','score':'','action':'unresolved','interval_ms':'3000','status':'resolved=false;reason=missing-rtt;control_applied=false'},
                  {'event':'WINDOW','node':'1','window_id':'2','rtt_ms':'8000','score':'0.4','action':'hold','interval_ms':'3000','status':'resolved=true;loss=0.2;ack=0.5;timeout=0.5'},
                  {'event':'WINDOW','node':'1','window_id':'3','rtt_ms':'8000','score':'','action':'none','interval_ms':'3000','status':'resolved=true;loss=0.2;ack=0.5;timeout=0.5;control_applied=false'},
                ])
            self.assertEqual([2],[r['window'] for r in window_rows(run)])
    def test_weight_name_falls_back_to_candidate_directory(self):
        p=Path('results/runs/calibration/moderate/depth15/proposed/reliability/seed-007')
        self.assertEqual('reliability',weight_name_from_manifest({},p))
    def test_guardrails_apply_to_depth_aggregates(self):
        fixed=[{'depth_case':'depth15','pdr_pct':60,'median_rtt_ms':100}]
        candidate=[{'depth_case':'depth15','pdr_pct':58.1,'median_rtt_ms':105}]
        self.assertTrue(candidate_meets_guardrails(candidate,fixed))
    def test_paired_effect_reports_relative_throughput(self):
        rows=[
          {'depth_case':'depth15','seed':11,'mode':'fixed','throughput_bps':100,'pdr_pct':60,'average_rtt_ms':10,'median_rtt_ms':10,'timeout_ratio_pct':20},
          {'depth_case':'depth15','seed':11,'mode':'proposed','throughput_bps':115,'pdr_pct':61,'average_rtt_ms':9,'median_rtt_ms':9,'timeout_ratio_pct':18},
        ]
        effect=compute_paired_effects(rows)[0]
        self.assertAlmostEqual(15,effect['throughput_change_pct'])
        self.assertAlmostEqual(1,effect['pdr_change_pp'])
        self.assertEqual(1,effect['pdr_ci95_low'])
        self.assertEqual(1,effect['pdr_ci95_high'])

    def test_v3_retries_and_duplicate_deliveries_do_not_inflate_useful_metrics(self):
        Path('tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='tmp') as td:
            run=Path(td)
            manifest={'status':'complete','protocol_version':'3','mode':'proposed','scenario':'moderate',
              'depth_case':'depth15','depth_m':15,'seed':9003,'measurement_s':10,
              'weights':[0.1,0.6,0.15,0.15],'controller_id':'candidate','fixed_interval_ms':3000}
            (run/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            fields='event,node,mode,scenario,depth_case,seed,seq,window_id,peer,time_ms,rtt_ms,interval_ms,score,pr,pl,pa,pt,action,payload_bytes,status,attempt,ack_requested'.split(',')
            def write(node,rows):
                with (run/f'events-node-{node}.csv').open('w',newline='',encoding='utf-8') as f:
                    out=csv.DictWriter(f,fields);out.writeheader();out.writerows(rows)
            base={k:'' for k in fields};base.update(mode='proposed',scenario='moderate',depth_case='depth15',seed='9003',window_id='1',peer='3',interval_ms='3000',payload_bytes='64')
            write(1,[
              base|{'event':'SEND','node':'1','seq':'1','time_ms':'60000','status':'DATA','attempt':'1','ack_requested':'false'},
              base|{'event':'SEND','node':'1','seq':'2','time_ms':'63000','status':'DATA','attempt':'1','ack_requested':'true'},
              base|{'event':'SEND','node':'1','seq':'1','time_ms':'66000','status':'RETRY','attempt':'2','ack_requested':'true'},
            ])
            write(2,[
              base|{'event':'DELIVER','node':'2','seq':'1','time_ms':'62000','attempt':'1'},
              base|{'event':'DUPLICATE_DATA','node':'2','seq':'1','time_ms':'67000','attempt':'2'},
            ])
            write(3,[base|{'event':'LATE_DATA','node':'3','seq':'2','time_ms':'71000','attempt':'1'}])
            row=summarize_run(run)
            self.assertEqual(2,row['unique_messages_generated'])
            self.assertEqual(3,row['transmission_attempts'])
            self.assertEqual(1,row['retry_attempts'])
            self.assertEqual(2,row['unique_messages_delivered'])
            self.assertAlmostEqual(100,row['pdr_pct'])
            self.assertAlmostEqual(102.4,row['throughput_bps'])
            self.assertAlmostEqual(100/3,row['retry_overhead_pct'])

    def test_depth_effect_is_paired_and_reports_verdict(self):
        rows=[]
        for seed,shallow,deep in ((1,100,110),(2,120,125),(3,90,100)):
            rows.extend([
              {'depth_case':'depth15','seed':seed,'mode':'fixed','throughput_bps':shallow},
              {'depth_case':'depth1000','seed':seed,'mode':'fixed','throughput_bps':deep},
            ])
        effect=compute_depth_effects(rows)[0]
        self.assertEqual('fixed',effect['mode'])
        self.assertAlmostEqual(25/3,effect['throughput_change_bps'])
        self.assertGreater(effect['throughput_ci95_low'],0)
        self.assertEqual('positive',effect['verdict'])
        rows[-1]['throughput_bps']=70
        self.assertEqual('inconclusive',compute_depth_effects(rows)[0]['verdict'])
    def test_smoke_run_summary(self):
        p=Path('tmp/integration-fixed-008')
        if not p.exists(): self.skipTest('integration fixture not present')
        row=summarize_run(p)
        self.assertEqual(10,row['packets_transmitted'])
        self.assertEqual(6,row['packets_received'])
        self.assertAlmostEqual(60.0,row['pdr_pct'])
        self.assertAlmostEqual(40.0,row['packet_loss_pct'])
        self.assertAlmostEqual(40.0,row['ack_ratio_pct'])
        self.assertAlmostEqual(60.0,row['timeout_ratio_pct'])
        self.assertAlmostEqual(102.4,row['throughput_bps'])

    def test_drain_delivery_counts_for_cohort_but_not_time_series(self):
        Path('tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='tmp') as td:
            run=Path(td)
            manifest={'status':'complete','protocol_version':'2','mode':'fixed','scenario':'moderate',
              'depth_case':'depth15','depth_m':15,'seed':1,'measurement_s':10,
              'weights':[0.1,0.6,0.15,0.15],'controller_id':'fixed','fixed_interval_ms':3000}
            (run/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            fields='event,node,mode,scenario,depth_case,seed,seq,window_id,peer,time_ms,rtt_ms,interval_ms,score,pr,pl,pa,pt,action,payload_bytes,status'.split(',')
            def write(node,rows):
                with (run/f'events-node-{node}.csv').open('w',newline='',encoding='utf-8') as f:
                    out=csv.DictWriter(f,fields);out.writeheader();out.writerows(rows)
            base={k:'' for k in fields};base.update(mode='fixed',scenario='moderate',depth_case='depth15',seed='1',window_id='1',peer='3',interval_ms='3000')
            write(1,[base|{'event':'SEND','node':'1','seq':'1','time_ms':'60000','payload_bytes':'64'}])
            write(2,[])
            write(3,[base|{'event':'LATE_DATA','node':'3','seq':'1','time_ms':'71000','payload_bytes':'64'}])
            row=summarize_run(run)
            self.assertEqual(1,row['packets_received'])
            self.assertAlmostEqual(51.2,row['throughput_bps'])
            self.assertEqual([(5.0,0.0)],time_binned_goodput(run,10))

    def test_control_overhead_and_unresolved_windows_are_reported(self):
        row=summarize_run(Path('results/v2/verification/agent-integration-fixed'))
        self.assertGreater(row['control_bytes'],0)
        self.assertGreaterEqual(row['unresolved_rate'],0)
        self.assertIn('precutoff_decisions',row)

    def test_duplicate_units_and_mixed_protocol_versions_fail(self):
        row={'protocol_version':'2','scenario':'moderate','depth_case':'depth15','seed':51,
             'mode':'fixed','controller_id':'fixed','fixed_interval_ms':3000}
        with self.assertRaises(ValueError):validate_run_set([row,row.copy()])
        other=row|{'seed':52,'protocol_version':'1'}
        with self.assertRaises(ValueError):validate_run_set([row,other])

    def test_formal_success_requires_every_gate(self):
        effects=[
          {'depth_case':'depth15','baseline':'fixed','throughput_change_pct':5.0,'throughput_ci95_low':0.1,'pdr_change_pp':5.0,'pdr_ci95_low':0.1},
          {'depth_case':'depth1000','baseline':'fixed','throughput_change_pct':5.0,'throughput_ci95_low':0.1,'pdr_change_pp':5.0,'pdr_ci95_low':0.1},
        ]
        verdict=evaluate_success(effects,{'depth15':[5,6,5],'depth1000':[5,5,7]})
        self.assertTrue(verdict['success'])
        effects[1]=effects[1]|{'pdr_ci95_low':0.0}
        self.assertFalse(evaluate_success(effects,{'depth15':[5],'depth1000':[5]})['success'])

if __name__=='__main__': unittest.main()
