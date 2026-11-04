import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from analysis.run_experiments import (
    PROTOCOL_VERSION, build_runs, controller_candidates, expected_manifest, validate_completed_run,
    prepare_run_directories, run_directory, run_one, simulator_output_failed,
)

class RunnerTests(unittest.TestCase):
    def test_paired_evaluation_matrix_has_both_depths(self):
        runs=build_runs('evaluation',seeds=[211],scenarios=['moderate'],frozen={
            'controller_id':'chosen','weights':[0.1,0.6,0.15,0.15],
            'rtt_reference_ms':10000,'healthy_threshold':0.5,
            'poor_threshold':0.7,'reliability_floor':0.5,'probe_margin':0.01,
            'retry_every_new':3,'max_retries_per_window':2})
        self.assertEqual(4,len(runs))
        self.assertEqual({'fixed','proposed'},{r['mode'] for r in runs})
        self.assertEqual({'depth15','depth1000'},{r['depth_case'] for r in runs})

    def test_seed_partitions_and_calibration_grid(self):
        self.assertEqual(set(range(181,186)),{r['seed'] for r in build_runs('screening')})
        self.assertEqual({201,202,203},{r['seed'] for r in build_runs('calibration')})
        self.assertEqual(set(range(211,231)),{r['seed'] for r in build_runs('evaluation',frozen={
            'controller_id':'chosen','weights':[0.1,0.6,0.15,0.15],'rtt_reference_ms':10000,
            'healthy_threshold':0.5,'poor_threshold':0.7,'reliability_floor':0.5,
            'probe_margin':0.01,'retry_every_new':3,'max_retries_per_window':2})})
        calibration=build_runs('calibration',seeds=[201])
        self.assertEqual({'fixed','proposed'},{r['mode'] for r in calibration})
        self.assertTrue(all(abs(sum(r['weights'])-1)<1e-9 for r in calibration))
        candidates=controller_candidates(0.5964285714285714)
        self.assertEqual(27,len(candidates))
        self.assertEqual({2,3,4},{r['retry_every_new'] for r in candidates})
        self.assertEqual({1,2,3},{r['max_retries_per_window'] for r in candidates})

    def test_completed_run_requires_exact_identity_and_event_files(self):
        row=build_runs('screening',seeds=[181],scenarios=['moderate'])[0]
        expected=expected_manifest(row,180)
        Path('tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='tmp') as td:
            path=Path(td)
            (path/'manifest.json').write_text(json.dumps({**expected,'status':'complete'}))
            for node in (1,2,3):(path/f'events-node-{node}.csv').write_text('event\n')
            validate_completed_run(path,expected)
            bad=dict(expected);bad['seed']=999
            with self.assertRaises(RuntimeError):validate_completed_run(path,bad)
            (path/'stdout.txt').write_text('SEVERE: Agent experiment died')
            with self.assertRaises(RuntimeError):validate_completed_run(path,expected)
            (path/'stdout.txt').write_text('EXPERIMENT_COMPLETE')
            (path/'events-node-3.csv').unlink()
            with self.assertRaises(RuntimeError):validate_completed_run(path,expected)

    def test_manifest_identity_includes_every_controller_parameter(self):
        frozen={'controller_id':'chosen','weights':[0.1,0.6,0.15,0.15],
            'rtt_reference_ms':12000,'healthy_threshold':0.55,
            'poor_threshold':0.75,'reliability_floor':0.58,'probe_margin':0.0}
        frozen.update(retry_every_new=3,max_retries_per_window=2)
        row=next(r for r in build_runs('evaluation',seeds=[211],frozen=frozen) if r['mode']=='proposed')
        identity=expected_manifest(row,600)
        self.assertEqual(PROTOCOL_VERSION,identity['protocol_version'])
        for key in ('controller_id','weights','rtt_reference_ms','healthy_threshold',
                    'poor_threshold','reliability_floor','probe_margin','measurement_s'):
            self.assertIn(key,identity)
        self.assertEqual('3',identity['protocol_version'])
        self.assertEqual('window-tail',identity['ack_policy'])
        self.assertEqual(3,identity['retry_every_new'])
        self.assertEqual(2,identity['max_retries_per_window'])

    def test_parallel_parent_directories_are_prepared_serially(self):
        Path('tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='tmp') as td:
            rows=build_runs('screening',seeds=[181])[:4]
            paths=prepare_run_directories(rows,'screening',Path(td))
            self.assertEqual(4,len(paths))
            self.assertTrue(all(path.is_dir() for path in paths))

    def test_simulator_severe_marker_is_failure_even_with_zero_exit(self):
        self.assertTrue(simulator_output_failed('SEVERE: Agent experiment died',''))
        self.assertTrue(simulator_output_failed('','Agent experiment died: boom'))
        self.assertFalse(simulator_output_failed('EXPERIMENT_COMPLETE path',''))

    def test_force_replaces_rejected_complete_manifest(self):
        row=build_runs('screening',seeds=[181])[0]
        Path('tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='tmp') as td:
            root=Path(td);out=run_directory(row,'screening',root);out.mkdir(parents=True)
            expected=expected_manifest(row,10)
            (out/'manifest.json').write_text(json.dumps({**expected,'status':'complete'}))
            for node in (1,2,3):(out/f'events-node-{node}.csv').write_text('event\n')
            (out/'stdout.txt').write_text('SEVERE: Agent experiment died')
            with patch('analysis.run_experiments.subprocess.run',return_value=SimpleNamespace(returncode=7,stdout='',stderr='')) as mocked:
                with self.assertRaisesRegex(RuntimeError,'simulator rc=7'):
                    run_one(row,'screening',10,True,root)
            mocked.assert_called_once()

if __name__=='__main__': unittest.main()
