# Lab Demo Runbook

## 1. Open PowerShell in the project root

```powershell
Set-Location "<repository-root>"
```

Always run from this directory because the simulation resolves `classes`, `scripts`, and `results` relative to the UnetStack root.

## 2. Verify tools

```powershell
java -version
python --version
.\bin\unet.bat
matlab -batch "disp(version)"
```

The bare UnetStack command prints its usage. Use the Java version bundled/supported by this UnetStack distribution on the lab machine.

## 3. Quick tests before the demo

```powershell
Get-ChildItem tests\*.groovy | ForEach-Object { & .\bin\unet.bat $_.FullName }
python -m unittest discover -s tests -p "test_*.py"
```

Do not delete or overwrite validated results just to perform a quick demo.

## 4. Run one fixed simulation manually

```powershell
$env:ADR_MODE = "fixed"
$env:ADR_SCENARIO = "moderate"
$env:ADR_DEPTH_CASE = "depth15"
$env:ADR_SEED = "231"
$env:ADR_MEASUREMENT_S = "180"
$env:ADR_OUTPUT_DIR = "results\demo\fixed-depth15-seed231"
& .\bin\unet.bat simulations\experiment.groovy
```

Expected completion marker:

```text
EXPERIMENT_COMPLETE results\demo\fixed-depth15-seed231
```

## 5. Run one proposed simulation manually

```powershell
$env:ADR_MODE = "proposed"
$env:ADR_SCENARIO = "moderate"
$env:ADR_DEPTH_CASE = "depth15"
$env:ADR_SEED = "231"
$env:ADR_MEASUREMENT_S = "180"
$env:ADR_OUTPUT_DIR = "results\demo\proposed-depth15-seed231"
$env:ADR_WEIGHTS = "0.15,0.55,0.15,0.15"
$env:ADR_RETRY_EVERY_NEW = "4"
$env:ADR_MAX_RETRIES_PER_WINDOW = "3"
& .\bin\unet.bat simulations\experiment.groovy
```

The same seed and depth make this a paired demonstration. Seed 231 is outside the frozen held-out set and does not alter the reported claim.

## 6. Re-run the complete frozen evaluation matrix

```powershell
python analysis/run_experiments.py evaluation `
  --config results/v3/calibration/frozen-config.json `
  --workers 8 `
  --measurement 180
```

This command creates or validates 80 units: 20 seeds x 2 depths x 2 modes. Existing complete matching units are reused. Add `--force` only when you intentionally want to replace those run directories.

## 7. Generate canonical summaries and figures

```powershell
python analysis/analyze_results.py `
  --runs results/v3/runs/evaluation `
  --output results/v3
```

Key outputs:

- `results/v3/summary/overall_comparison.csv`
- `results/v3/summary/paired_effects.csv`
- `results/v3/summary/depth_effects.csv`
- `results/v3/summary/success.json`
- `results/v3/figures/*.png` and `*.pdf`

## 8. Draw the final graphs in MATLAB

Command-line method:

```powershell
matlab -batch "run('analysis/analyze_final_results.m')"
```

MATLAB desktop method:

```matlab
cd('<repository-root>')
run('analysis/analyze_final_results.m')
```

MATLAB reads the validated CSV files from `results/v3/summary` and writes PNG and vector-PDF figures to `results/v3/matlab_figures`.

## 9. What to show the TA

1. `simulations/experiment.groovy` for topology and duration.
2. `classes/AdaptiveExperimentAgent.groovy` for message flow.
3. `classes/RetryScheduler.groovy` for ACK thinning and bounded retry.
4. `results/v3/calibration/frozen-config.json` for frozen parameters.
5. `results/v3/summary/overall_comparison.csv` for exact final means.
6. `results/v3/summary/paired_effects.csv` for effect sizes and confidence intervals.
7. `results/v3/matlab_figures/matlab_final_dashboard.png` for the MATLAB result view.

## 10. Short viva script

"Our official baseline sends one 64-byte message every 3000 ms, requests every ACK, and has no application retry. Proposed v3 samples two original ACKs per ten-message window and retries only receiver-confirmed missing IDs, with one retry after four new originals and at most three per window. We count unique IDs, so retries cannot inflate throughput. Across 20 paired held-out seeds at each depth, throughput improved by 30.63% and 24.30%, while PDR improved by 22.48 and 19.26 percentage points. Depth did not universally increase throughput."

## 11. Cleanup after manual demo

The manual demo writes only under `results/demo`. Keep it if you need the logs for the presentation. Do not mix demo rows into `results/v3/runs/evaluation` or overwrite the frozen evaluation data.
