# Code Walkthrough: Implemented Protocol Version 3

## Execution path

```text
analysis/run_experiments.py
  -> bin/unet.bat simulations/experiment.groovy
  -> node setup scripts
  -> AdaptiveExperimentAgent
  -> ProtocolCodec + ExperimentState + RetryScheduler + AdaptiveRateController
  -> isolated event CSV and manifest
analysis/analyze_results.py
  -> validated summary CSV + Python figures
analysis/analyze_final_results.m
  -> MATLAB figures from the same validated summary CSV
```

## Main source files

| File | Current responsibility |
|---|---|
| `simulations/experiment.groovy` | Finite three-node simulation, topology, duration, modem rate, manifest |
| `scripts/adaptive-setup-a.groovy` | Sender node stack and experiment agent |
| `scripts/adaptive-setup-b.groovy` | Receiver node stack and experiment agent |
| `classes/ExperimentConfig.groovy` | Validated environment configuration and manifest fields |
| `classes/AdaptiveExperimentAgent.groovy` | Pacing, DATA/ACK/report handling, cutoff, event logging |
| `classes/ProtocolCodec.groovy` | Version-3 DATA, ACK, report-request, and report formats |
| `classes/ExperimentState.groovy` | Unique original, attempt, delivery, ACK, timeout, and window state |
| `classes/ReceiverFeedbackState.groovy` | Receiver delivery sets and immutable snapshots |
| `classes/RetryScheduler.groovy` | ACK thinning, retry queue, cadence, retry cap, interval latch |
| `classes/AdaptiveRateController.groovy` | Four-metric score and candidate-interval decision |
| `classes/ScenarioChannelModel.groovy` | Good, moderate, poor, and step channel probabilities |
| `analysis/run_experiments.py` | Paired matrix orchestration, run identity, failure detection |
| `analysis/analyze_results.py` | Unique-message metrics, bootstrap effects, figures, success gates |
| `analysis/analyze_final_results.m` | MATLAB reproduction of final summary figures |

## DATA and feedback flow

1. Node A creates a stable sequence ID and alternates destinations B and C.
2. Fixed mode requests an ACK for every original. Proposed mode requests ACKs for only the last two originals of each ten-original window.
3. A receiver records each unique sequence ID. A sampled ACK can carry the first immutable snapshot of the previous window.
4. The sender compares expected IDs with that snapshot. Only confirmed missing IDs enter the retry queue.
5. One retry opportunity becomes eligible after four new originals. A window reserves at most three retries, and a sequence can be attempted at most twice.
6. Originals and retries share one paced scheduler, so recovery does not create an uncontrolled parallel stream.
7. The analyzer counts unique IDs, not attempts. Duplicate or late deliveries cannot inflate throughput or PDR.

## Four controller inputs

The score combines normalized RTT penalty, confirmed loss ratio, ACK-failure penalty, and timeout ratio. Frozen weights are 0.15, 0.55, 0.15, and 0.15. Confirmed loss has the greatest influence because the receiver snapshot directly reports delivery.

The controller uses candidate intervals rather than an unbounded multiplication rule. A selected interval is latched for the full original window, preventing mid-window pacing changes.

## Legacy mode

Legacy reacts to individual ACKs and timeouts: it raises the interval when RTT/timeout conditions look poor and lowers it after healthier ACKs. This older method is retained for code history, but the final held-out experiment compares only fixed and proposed modes.

## Depth handling

Node A and B remain at 15 m. Node C is placed at 15 m or 1000 m while its horizontal coordinate remains 2 km from A. In the selected `ProtocolChannelModel`, this changes 3D range and propagation/collision timing. It does not automatically improve the configured detection or decoding probabilities.

## Verification

The completed verification record reports seven Groovy test scripts passing, 23 Python tests passing, all 80 held-out units matching the frozen manifest, and no severe simulation marker in the evaluation logs. See `results/v3/verification/FINAL_VERIFICATION.md`.
