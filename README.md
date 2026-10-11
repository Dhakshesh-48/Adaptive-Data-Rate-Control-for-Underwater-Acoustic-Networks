# Adaptive Data Rate Control for Underwater Acoustic Networks

An academic project exploring an adaptive data-rate control mechanism for underwater acoustic networks using **Round-Trip Time (RTT)** and **packet-loss information**.

## Overview

Underwater acoustic networks support applications such as ocean monitoring, marine research, and underwater exploration. However, underwater communication is challenging because of limited bandwidth, high propagation delay, noise, multipath effects, node movement, and changing distances between nodes.

A fixed transmission rate may perform well under stable channel conditions but can lead to increased packet loss when conditions deteriorate. Conversely, always using a low transmission rate can reduce throughput.

This project aims to investigate an adaptive approach that adjusts the transmission rate according to observed RTT and packet loss.

## Objectives

- Develop a method to adjust the transmission rate using RTT and packet-loss information.
- Test the proposed approach under different channel conditions using **UnetStack**.
- Compare adaptive-rate transmission with fixed-rate transmission.
- Evaluate performance using throughput, packet loss, and RTT.

## Proposed Approach

1. **Set up the simulation:** Configure an underwater acoustic network scenario in UnetStack.
2. **Establish a baseline:** Run experiments using a fixed transmission rate.
3. **Collect feedback:** Observe RTT and packet-loss information under the simulated channel conditions.
4. **Adapt the rate:** Use the observed feedback to select an appropriate transmission rate.
5. **Run comparative experiments:** Test both approaches under stable and changing channel conditions.
6. **Analyse results:** Use MATLAB to analyse and compare the performance measurements.

> The exact rate-adjustment rule and experimental configuration will be documented as the implementation develops.

## Evaluation Metrics

| Metric | Purpose |
|---|---|
| Throughput | Measures the amount of data successfully delivered over time. |
| Packet loss | Measures the proportion of transmitted packets that are not successfully received. |
| Round-Trip Time (RTT) | Measures the time taken for a packet to travel to a destination and for a response to return. |

The main comparison is between **adaptive-rate transmission** and **fixed-rate transmission** under different channel conditions.

## Technology Stack

- **UnetStack** — underwater network simulation and experimentation.
- **MATLAB** — analysis and comparison of experimental results.

## Getting Started

### Prerequisites

- UnetStack installed and configured.
- MATLAB for analysing experimental results.
- The simulation scripts and configuration files developed for this project.

### Run the Project

The run instructions depend on the simulation scripts and configuration files in the repository. Once those files are available:

1. Open the project in your UnetStack environment.
2. Run the relevant simulation script.
3. Save the measurements for each experiment.
4. Analyse the collected results in MATLAB.

**Note:** Exact commands and script names will be added after the repository's implementation structure is finalised.

## Expected Outcome

The project will compare adaptive and fixed-rate transmission under stable and changing underwater channel conditions. The evaluation will focus on throughput, packet loss, and RTT to understand how feedback-based rate adjustment affects communication performance.

These are intended evaluation goals; measured results will be reported after the experiments are completed.

## Repository Structure

The structure below is a suggested organisation. Update it to match the actual files in this repository.

```text
.
├── README.md
├── simulations/    # UnetStack simulation scripts
├── results/        # Experiment outputs and collected measurements
└── analysis/       # MATLAB scripts for result analysis
```

## Team Members

- **M Dhakshesh Naidu** — 241CS132
- **Pratham M Attavar** — 241CS142
- **S Nikhil** — 241CS158

## References

1. I. F. Akyildiz, D. Pompili, and T. Melodia, “Underwater acoustic sensor networks: Research challenges,” *Ad Hoc Networks*, vol. 3, no. 3, pp. 257–279, 2005. https://doi.org/10.1016/j.adhoc.2005.01.004
2. UnetStack, *Underwater Networks Handbook*, version 3.3.0. https://unetstack.net/handbook/
3. UnetStack, “UnetStack: The underwater network stack.” https://unetstack.net/

## Project Status

**In progress.** The project proposes an RTT- and packet-loss-based adaptive data-rate approach. Simulation, implementation details, and performance results will be added as they become available.
