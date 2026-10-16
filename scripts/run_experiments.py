"""Run reproducible forecasting comparisons; not a substitute for the full A/B/C experiment."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from psrs.services.demand_forecasting import forecast_demand
from psrs.services.synthetic_data import generate_dataset

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def run(output_dir: Path, seed: int, historical_days: int, forecast_days: int) -> dict:
    generate_dataset(output_dir, seed=seed, historical_days=historical_days, forecast_days=forecast_days)
    history = read_csv(output_dir / "demand_history.csv")
    truth = read_csv(output_dir / "evaluation_ground_truth.csv")
    keys = sorted({(r["location_id"], r["item_id"]) for r in history})
    results = []
    for location_id, item_id in keys:
        actual_rows = sorted((r for r in truth if r["location_id"] == location_id and r["item_id"] == item_id), key=lambda r: r["date"])
        actual = [int(r["actual_demand_units"]) for r in actual_rows]
        for model in ("baseline", "ml", "auto"):
            forecast = forecast_demand(history, location_id, item_id, len(actual), model)
            errors = [abs(a - p) for a, p in zip(actual, forecast.predictions)]
            denom = sum(abs(a) for a in actual)
            results.append({"location_id": location_id, "item_id": item_id, "configuration": model,
                "mae": sum(errors) / len(errors) if errors else None,
                "wape": (sum(errors) / denom * 100) if denom else None,
                "forecast_model": forecast.model})
    summary = {}
    for model in ("baseline", "ml", "auto"):
        values = [r["mae"] for r in results if r["configuration"] == model and r["mae"] is not None]
        summary[model] = {"mean_series_mae": round(sum(values) / len(values), 4) if values else None}
    report = {"seed": seed, "historical_days": historical_days, "forecast_days": forecast_days,
        "synthetic_only": True, "scope": "forecasting-only; does not establish full A/B/C logistics performance",
        "summary": summary, "results": results}
    (output_dir / "forecast_experiment_results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/experiment")
    parser.add_argument("--seed", type=int, default=26251)
    parser.add_argument("--historical-days", type=int, default=90)
    parser.add_argument("--forecast-days", type=int, default=14)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.output), args.seed, args.historical_days, args.forecast_days)["summary"], indent=2))

if __name__ == "__main__":
    main()
