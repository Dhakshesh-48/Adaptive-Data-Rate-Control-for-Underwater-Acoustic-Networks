# Final Experiment and Results Guide

## Research question

Under identical simulated conditions, does protocol v3 improve useful throughput and packet-delivery ratio over a fixed 3000 ms application sending interval?

## Controlled design

- Simulator: UnetStack 7.0.0 discrete-event simulation.
- Channel: moderate `ProtocolChannelModel` condition.
- Topology: A, B, C at horizontal positions 0, 1, and 2 km; A/B at 15 m; C tested at 15 m and 1000 m.
- DATA size: 64 bytes, or 512 useful bits.
- Warm-up: 60 s; measurement: 180 s; post-cutoff drain enabled.
- Evaluation: seeds 211-230, paired across fixed and proposed at both depths.
- Independent replicate: one complete seeded run, not an individual packet.
- Frozen candidate: `w2-e4-c3`, selected before held-out evaluation.

## Data partitions

| Partition | Seeds | Purpose | Units |
|---|---|---|---:|
| Screening | 181-185 | Candidate exploration | 280 |
| Calibration | 201-210 | Freeze one candidate | 112 |
| Held-out evaluation | 211-230 | Final fixed/proposed claim | 80 |

## Metrics

- Unique generated: original attempt-1 IDs created during measurement.
- Transmission attempts: originals plus retries.
- Unique delivered: generated IDs observed at either receiver, counted once.
- PDR: unique delivered divided by unique generated.
- Useful throughput: unique delivered times 512 bits divided by 180 s.
- Retry overhead: retry attempts divided by all DATA attempts.
- RTT: ACK arrival time minus the send time of its matching attempt.
- Timeout ratio: deadline expirations relative to the relevant ACK-requested attempts.

## Final means

| Depth | Mode | Generated | Attempts | Delivered | PDR | Throughput | Retry overhead |
|---|---|---:|---:|---:|---:|---:|---:|
| 15 m | Fixed | 60.00 | 60.00 | 36.05 | 60.08% | 102.54 bit/s | 0.00% |
| 15 m | Proposed | 56.75 | 60.00 | 46.85 | 82.57% | 133.26 bit/s | 5.42% |
| 1000 m | Fixed | 60.00 | 60.00 | 37.45 | 62.42% | 106.52 bit/s | 0.00% |
| 1000 m | Proposed | 56.90 | 60.00 | 46.45 | 81.68% | 132.12 bit/s | 5.17% |

## Paired effects

| Depth | Throughput change (95% CI) | PDR change (95% CI) |
|---|---:|---:|
| 15 m | +30.63% (+25.71 to +35.44) | +22.48 points (+20.66 to +24.35) |
| 1000 m | +24.30% (+21.00 to +27.58) | +19.26 points (+17.54 to +21.01) |

The formal target was at least +5% throughput and +5 PDR percentage points at both depths, with paired 95% bootstrap intervals excluding zero. All four gates passed.

## Depth conclusion

The observed `1000 m - 15 m` throughput difference was +3.98 bit/s for fixed mode (95% CI +0.57 to +7.82) and -1.14 bit/s for proposed mode (95% CI -3.56 to +1.42). Do not claim that increasing depth universally increases throughput.

## Reproduction

```powershell
python analysis/run_experiments.py evaluation --config results/v3/calibration/frozen-config.json --workers 8 --measurement 180
python analysis/analyze_results.py --runs results/v3/runs/evaluation --output results/v3
matlab -batch "run('analysis/analyze_final_results.m')"
```

The Python analyzer is the canonical statistical pipeline. MATLAB reads its validated CSV outputs and independently recreates the final presentation figures.
