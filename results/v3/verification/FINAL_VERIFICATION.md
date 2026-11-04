# Final verification - protocol version 3

Date: 2026-10-30

## Fresh verification

- Groovy: 7/7 scripts passed (`PROTOCOL`, `STATE`, `RETRY_SCHEDULER`, `AGENT_STATE`, `CONTROLLER`, `SCENARIO`, `SMOKE`).
- Python: 23/23 tests passed.
- Evaluation matrix: 80/80 exact units validated against frozen manifest identity.
- Evaluation marker scan: no `SEVERE:` or `Agent experiment died` marker.
- PDF: reopened successfully, 5/5 pages contain text, and all rendered pages were visually inspected.
- Figures: throughput and PDR figures visually inspected with no clipping or layout defect.
- Complete handbook PDF: reopened successfully, 26/26 pages contain text, and all rendered pages were visually inspected after correcting code contrast and appendix page breaks.
- MATLAB R2026b: `analysis/analyze_final_results.m` executed successfully against the validated CSV summaries and exported 10 PNG plus 10 vector-PDF figures.

## Held-out success gates

| Depth | Throughput gain | 95% CI | PDR gain | 95% CI | Result |
|---|---:|---:|---:|---:|---|
| 15 m | +30.63% | +25.71% to +35.44% | +22.48 pp | +20.66 to +24.35 pp | PASS |
| 1000 m | +24.30% | +21.00% to +27.58% | +19.26 pp | +17.54 to +21.01 pp | PASS |

Formal target: at least +5% useful throughput and +5 PDR percentage points at both depths, with paired 95% intervals excluding zero.

## Depth inference

- Fixed `1000 m - 15 m`: +3.98 bit/s, 95% CI +0.57 to +7.82 (positive for fixed mode).
- Proposed `1000 m - 15 m`: -1.14 bit/s, 95% CI -3.56 to +1.42 (inconclusive).
- Conclusion: do not claim that throughput generally increases with depth.

## SHA-256

- `44CDDADA85B95BDCBC728162D5349ACCB0B78B8EF2E483008CD5D14FAFCA6389` - `output/pdf/TA_Progress_Report_Protocol_v3.pdf`
- `204C32661A737132978CD66F805E93AE8780FBE7B092F4D2DC80AC32DD720018` - `results/v3/calibration/frozen-config.json`
- `AC5FE0FA66D7A77D02AA5E8B7BAC793C00454128D6107BC25AC386E70B14E882` - `results/v3/summary/paired_effects.csv`
- `1E35DCE3EF2015F302A99774722956BD7B46178AB373485D1E26DDA228A53D74` - `output/pdf/Complete_Project_and_Lab_Handbook_Protocol_v3.pdf`

## Final artifacts

- TA PDF: `output/pdf/TA_Progress_Report_Protocol_v3.pdf`
- Complete project/lab handbook: `output/pdf/Complete_Project_and_Lab_Handbook_Protocol_v3.pdf`
- Results explanation: `docs/FINAL_RESULTS.md`
- Algorithm explanation: `docs/PROJECT_EXPLANATION.md`
- Lab commands: `docs/DEMO_RUNBOOK.md`
- MATLAB figures: `results/v3/matlab_figures/`
- Frozen configuration: `results/v3/calibration/frozen-config.json`
- Per-run summary: `results/v3/summary/run_summary.csv`
- Figures: `results/v3/figures/`
