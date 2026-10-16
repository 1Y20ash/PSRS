# Experimental Design

The planned comparison has three configurations:

- **A — Recorded-stock baseline:** recorded inventory values plus a statistical demand baseline.
- **B — Reconciliation-only:** reconstructed inventory plus the same statistical demand baseline.
- **C — Integrated PSRS:** inventory uncertainty, selected forecast, GIS route costs and feasibility, synthetic disruptions, and shared transportation capacity.

Configurations should use comparable synthetic scenarios, evaluation periods, hard constraints, and a documented objective. Results must be reported even if the integrated approach performs worse or gives mixed results.

The current `scripts/run_experiments.py` performs a forecasting-only baseline/ML/automatic comparison. It is not the full A/B/C logistics experiment. The dashboard's nominal/adverse scenario workflow is a heuristic demonstration and does not prove comparative improvement.

The full A/B/C experiment remains pending until observed inventory discrepancies and hidden inventory ground truth are modeled explicitly, all configurations run on the same scenarios and constraints, and the agreed inventory, forecast, shortage, route, capacity, regret, runtime and reproducibility metrics are calculated. Never claim improvement before those runs finish.
