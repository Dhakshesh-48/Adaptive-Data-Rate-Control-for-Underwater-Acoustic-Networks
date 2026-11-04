# Start Here: Protocol Version 3

## Project in one sentence

We compare a fixed 3000 ms application sending interval with a receiver-validated adaptive protocol that reduces ACK traffic and performs a small number of selective retries for confirmed missing messages.

## The problem

Underwater acoustic networks have long propagation delays, limited bandwidth, half-duplex links, and losses. A fixed sender cannot react to the observed network state: sending too aggressively can create collisions and timeouts, while sending too slowly wastes capacity.

## The official comparison

| Item | Fixed baseline | Proposed protocol v3 |
|---|---|---|
| Sending interval | Always 3000 ms | Window-latched adaptive candidate interval |
| Original ACKs | Every original | Last two originals in each ten-message window |
| Application retries | None | Receiver-confirmed missing IDs only |
| Retry bound | Not applicable | At most one retry per ID and three per window |
| Retry cadence | Not applicable | One retry opportunity after four new originals |

Legacy is an older adaptive controller retained in the code for historical study. It is not the official baseline and is not part of the held-out fixed-versus-proposed claim.

## Frozen proposed parameters

- Weights: `[0.15, 0.55, 0.15, 0.15]` for RTT, confirmed loss, ACK failure, and timeout.
- Window size: 10 originals.
- Candidate intervals: 2000, 2250, 2500, 2700, 3000, 3375, 3750, 4500, and 6000 ms.
- One retry opportunity after four new originals.
- At most three retries originating from a window.
- At most two DATA attempts for one stable sequence ID.

The loss weight is largest because an immutable receiver snapshot is direct evidence of which unique IDs arrived.

## Honest metrics

- `PDR = unique delivered / unique generated`.
- `useful throughput = unique delivered x 512 bits / 180 seconds`.
- `retry overhead = retry DATA attempts / all DATA attempts`.
- A retry can recover an existing sequence ID but cannot create a new useful message in the denominator.

## Final held-out result

Twenty paired evaluation seeds were used at each depth. Compared with fixed 3000 ms, proposed v3 improved useful throughput by 30.63% at 15 m and 24.30% at 1000 m. PDR improved by 22.48 and 19.26 percentage points. All four paired 95% bootstrap intervals excluded zero.

Depth itself did not have a universal positive effect. Fixed mode increased by 3.98 bit/s from 15 m to 1000 m, while proposed mode changed by -1.14 bit/s and its interval crossed zero.

## Run the complete workflow

From the repository root in PowerShell:

```powershell
python analysis/run_experiments.py evaluation --config results/v3/calibration/frozen-config.json --workers 8 --measurement 180
python analysis/analyze_results.py --runs results/v3/runs/evaluation --output results/v3
matlab -batch "run('analysis/analyze_final_results.m')"
```

For a detailed walkthrough, read `docs/CODE_WALKTHROUGH.md`. For exact demo commands, read `docs/DEMO_RUNBOOK.md`.
