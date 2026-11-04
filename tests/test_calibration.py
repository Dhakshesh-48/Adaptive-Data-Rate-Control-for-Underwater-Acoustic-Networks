import unittest
from analysis.calibrate_controller import derive_reliability_floor, screen_candidates, select_candidate

class CalibrationTests(unittest.TestCase):
    def test_floor_is_smaller_depth_fixed_mean_minus_two_points(self):
        fixed=[
          {'depth_case':'depth15','pdr_pct':70.0}, {'depth_case':'depth15','pdr_pct':74.0},
          {'depth_case':'depth1000','pdr_pct':65.0}, {'depth_case':'depth1000','pdr_pct':67.0},
        ]
        self.assertAlmostEqual(0.64,derive_reliability_floor(fixed))

    def test_selection_requires_both_five_percent_targets_and_breaks_ties_by_overhead(self):
        rows=[]
        for depth in ('depth15','depth1000'):
          for seed in (201,202):
            rows.append({'controller_id':'fixed','mode':'fixed','depth_case':depth,'seed':seed,
              'throughput_bps':100.0,'pdr_pct':70.0,'median_rtt_ms':100.0,'control_bytes':0,'unresolved_rate':0})
            rows.append({'controller_id':'a','mode':'proposed','depth_case':depth,'seed':seed,
              'throughput_bps':106.0,'pdr_pct':75.0,'retry_overhead_pct':4,'control_bytes':20})
            rows.append({'controller_id':'b','mode':'proposed','depth_case':depth,'seed':seed,
              'throughput_bps':106.0,'pdr_pct':75.0,'retry_overhead_pct':4,'control_bytes':10})
        chosen=select_candidate(rows,['a','b'])
        self.assertEqual('b',chosen['controller_id'])
        self.assertAlmostEqual(6.0,chosen['minimum_depth_gain_pct'])

    def test_no_guardrail_candidate_is_an_explicit_failure(self):
        rows=[]
        for depth in ('depth15','depth1000'):
          rows += [
            {'controller_id':'fixed','mode':'fixed','depth_case':depth,'seed':201,'throughput_bps':100,'pdr_pct':70,'control_bytes':0,'retry_overhead_pct':0},
            {'controller_id':'bad','mode':'proposed','depth_case':depth,'seed':201,'throughput_bps':120,'pdr_pct':74.9,'control_bytes':1,'retry_overhead_pct':1},
          ]
        with self.assertRaises(RuntimeError):select_candidate(rows,['bad'])

    def test_screening_advances_exactly_four_candidates_deterministically(self):
        rows=[]
        for depth in ('depth15','depth1000'):
          rows += [
            {'controller_id':'fixed','mode':'fixed','depth_case':depth,'seed':201,'throughput_bps':100,'pdr_pct':70,'control_bytes':0,'retry_overhead_pct':0},
          ]
          for i,gain in enumerate((4,5,6,7,8),1):
            rows.append({'controller_id':f'c{i}','mode':'proposed','depth_case':depth,'seed':201,
              'throughput_bps':100+gain,'pdr_pct':75,'control_bytes':i,'retry_overhead_pct':i})
        self.assertEqual(['c5','c4','c3','c2'],screen_candidates(rows,['c1','c2','c3','c4','c5'],4))

if __name__=='__main__':unittest.main()
