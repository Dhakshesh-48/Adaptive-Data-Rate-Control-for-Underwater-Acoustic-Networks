# Version-3 calibration verification

Date completed: 2026-10-30

- Screening: 280/280 units, seeds 181-185, two depths, fixed plus 27 proposed candidates.
- Calibration stage 1: 42/42 units, seeds 201-203, fixed plus six proposed candidates.
- Calibration stage 2: 70/70 units, seeds 204-210, fixed plus four advanced candidates.
- Combined calibration set: 112 unique experimental units.
- Held-out seeds 211-230 were not accessed before configuration freeze.

Frozen candidate: `w2-e4-c3`

- Weights: `[0.15, 0.55, 0.15, 0.15]`
- Retry cadence: one eligible retry after four new originals
- Retry cap: three retries per original window
- ACK policy: final original to each receiver plus all retries
- Minimum depth-specific paired mean throughput gain: `+30.6882%`
- Minimum depth-specific paired mean PDR gain: `+20.9168 percentage points`

The frozen machine-readable configuration is
`results/v3/calibration/frozen-config.json`.
