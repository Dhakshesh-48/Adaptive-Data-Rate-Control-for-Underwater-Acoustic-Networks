# Final verification

- UnetStack 7.0.0; Java 1.8.0_471
- Calibration: seeds 1–10, five proposed weight candidates at two depths plus fixed baselines (120 runs)
- Evaluation: seeds 11–30, three modes at two depths (120 runs)
- Measurement: 180 simulated seconds per run
- Selected weights: `[0.20, 0.25, 0.20, 0.35]`
- Python tests: 6 passed
- Groovy controller, state, protocol, and scenario suites: passed
- Tables and requested PNG/PDF figures: generated
- Tested platform: Windows; macOS/Linux launchers were not executed locally
- Conclusion: proposed throughput is statistically indistinguishable from fixed and approximately 103–106% higher than legacy adaptive mode.
