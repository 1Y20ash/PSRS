# Evaluation Results

## Status

The full PDP A/B/C logistics experiment has not been completed. Forecasting-only metrics do not prove that integrated planning improves logistics outcomes.

## Reproducible forecasting experiment

Run:

    python scripts/run_experiments.py --seed 26251 --historical-days 90 --forecast-days 14

The script generates synthetic data and compares baseline, ML, and automatic model selection across fictional location-item series. It writes forecast_experiment_results.json with seed, window sizes, model choices, MAE, and WAPE. Ground truth is read only after predictions have been produced.

This is forecasting-only evidence. It does not evaluate inventory uncertainty propagation, GIS feasibility, transport capacity, route disruption, decision regret, or configurations A/B/C.

## Full A/B/C results

Pending implementation and execution of the integrated scenario runner. Record actual metrics, exact code commit SHA, seed, scenario assumptions, metric definitions, and limitations only after a successful run. Never fabricate results.
