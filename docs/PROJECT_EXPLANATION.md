# How the Project Works

## One-line explanation

The proposed application-layer controller reduces unnecessary ACK traffic and uses a small number of receiver-confirmed retries, increasing both useful throughput and reliability without changing the modem, MAC, topology, or channel probabilities.

## Fixed baseline versus proposed mode

| Item | Fixed baseline | Proposed protocol v3 |
|---|---|---|
| Original pacing | Every 3000 ms | Adaptive, window-latched pacing |
| Original ACK policy | ACK every message | Two per ten-message window |
| Retries | None | Missing IDs only; at most one retry per ID |
| Retry cadence | None | One eligible retry after four new originals |
| Retry cap | None | Three per original window |
| Useful denominator | Unique originals | Unique originals; retries never enlarge it |

## Message flow

```text
Node A                                      Node B / Node C
  |-- DATA(window, seq, attempt=1, ack?) -------->|
  |                                                | records unique seq
  |<-- sampled ACK + frozen previous snapshot -----|
  |-- DATA(same seq, attempt=2, ack=true) -------->|  only if snapshot says missing
  |<-- retry ACK ----------------------------------|
```

Every DATA frame remains 64 bytes. A stable sequence ID represents one useful application message; `attempt=2` recovers the same message and is not a new PDR/throughput item.

## Each frozen parameter

- `weights = [0.15, 0.55, 0.15, 0.15]`: importance of RTT, confirmed loss, ACK failure, and timeout. Confirmed loss is highest because receiver snapshots are direct delivery evidence.
- `windowSize = 10`: feedback and control operate on ten originals.
- `retryEveryNew = 4`: after four new originals, one queued retry may use the next paced opportunity.
- `maxRetriesPerWindow = 3`: a window creates at most three retries.
- `attempt <= 2`: each sequence is retried at most once.
- `fixedIntervalMs = 3000`: unchanged official baseline.
- Candidate intervals: `2000, 2250, 2500, 2700, 3000, 3375, 3750, 4500, 6000` ms.

Pacing is latched for a complete original window, so a previous-window decision cannot change the interval halfway through the next window.

## Receiver-validated recovery

The first valid snapshot for each receiver/window is immutable for online decisions. It divides expected IDs into delivered and missing. Missing IDs enter a deterministic bounded queue. A later retry can add one unique final delivery but cannot rewrite the controller’s historical snapshot.

## Honest metrics

- Unique generated: attempt-1 IDs created during measurement.
- Transmission attempts: originals plus retries.
- Unique delivered: generated IDs seen at either receiver, including drain-time arrivals.
- PDR: unique delivered / unique generated.
- Useful throughput: unique delivered × 512 bits / 180 s.
- Retry overhead: retry attempts / all DATA attempts.

Duplicates and retries cannot inflate useful results.

## Experiment design

UnetStack simulates nodes at horizontal positions 0, 1, and 2 km. A and B stay at 15 m; C is evaluated at 15 m and 1000 m. Paired comparisons use identical seeds, topology, payload, channel, warm-up, and duration.

- Screening: seeds 181–185
- Calibration: seeds 201–210
- Held-out evaluation: seeds 211–230
- Warm-up: 60 s; measurement: 180 s

The configuration was frozen before any held-out seed ran.

## Final answer for the TA

Compared with fixed 3000 ms, proposed mode improved useful throughput by **30.63% at 15 m** and **24.30% at 1000 m**. PDR improved by **22.48** and **19.26 percentage points**. All paired 95% bootstrap intervals exclude zero. Retry overhead was about **5.2–5.4%**.

Do not say “throughput always increases with depth.” Fixed mode had a positive depth effect here, but proposed mode’s depth interval included zero.

## Main files and commands

| File | Responsibility |
|---|---|
| `classes/AdaptiveExperimentAgent.groovy` | paced originals/retries, sparse ACKs, feedback |
| `classes/RetryScheduler.groovy` | retry order, cadence/cap, ACK policy, interval latch |
| `classes/ExperimentState.groovy` | unique IDs, attempts, ACKs, snapshots, metrics |
| `classes/ProtocolCodec.groovy` | protocol-v3 messages |
| `analysis/run_experiments.py` | paired orchestration and validation |
| `analysis/analyze_results.py` | metrics, inference, figures |

```powershell
python analysis/run_experiments.py evaluation --config results/v3/calibration/frozen-config.json --workers 8 --measurement 180
python analysis/analyze_results.py --runs results/v3/runs/evaluation --output results/v3
```
