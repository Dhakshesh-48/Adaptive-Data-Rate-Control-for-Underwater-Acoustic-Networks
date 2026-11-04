# Adaptive Data Rate Control for Underwater Acoustic Networks

Computer Networks mini project implemented with UnetStack 7.0.0 and analysed in MATLAB.

## Team

- 241CS132 - M. Dhakshesh Naidu
- 241CS142 - Pratham M. Attavar
- 241CS158 - Srikara Nikhil

## Approach

The fixed baseline sends every 3000 ms. The corrected legacy controller changes its interval using ACK RTT and timeout feedback. The implemented proposed controller combines RTT, confirmed receiver-side loss, ACK ratio, and timeout ratio over packet windows while keeping its interval between 1000 ms and 10000 ms.

The improvement must be demonstrated by controlled fixed-versus-adaptive experiments using ACK ratio, throughput, RTT, timeouts/loss, and interval behaviour.

## Repository Layout

- `classes/AdaptiveExperimentAgent.groovy` - mode-selectable sender and receiver agent
- `simulations/` - UnetStack simulation entry points
- `scripts/` - node stack setup
- `results/` - isolated raw runs, final summaries, and figures
- `analysis/analyze_results.py` - validated summary and figure pipeline
- `analysis/analyze_final_results.m` - MATLAB final-summary plots
- `INFO.md` - authoritative project context and current status

## Understand the Project

Read these files in order:

1. [`docs/START_HERE.md`](docs/START_HERE.md) - plain-language project explanation
2. [`docs/CODE_WALKTHROUGH.md`](docs/CODE_WALKTHROUGH.md) - current code and planned changes
3. [`docs/EXPERIMENT_GUIDE.md`](docs/EXPERIMENT_GUIDE.md) - metrics, experiments, plots, and result interpretation
4. [`docs/PROJECT_EXPLANATION.md`](docs/PROJECT_EXPLANATION.md) - implemented architecture and packet flow
5. [`docs/FINAL_RESULTS.md`](docs/FINAL_RESULTS.md) - final tables, graphs, and evidence-bounded conclusion

## Run

Run commands from this repository root so UnetStack can find the custom classes and scripts.

```powershell
python analysis/run_experiments.py --demo-set --workers 2
python analysis/analyze_results.py --runs results/runs --output results
```

The held-out results are reproducible from the saved manifests and raw event logs. They do not support a 10–15% improvement over fixed mode; see the final results document before making claims.
