"""Deterministic synthetic data generation for PSRS research experiments.

All locations and quantities are fictional. Evaluation ground truth is written
to a separate file and must not be used as an input to planning algorithms.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

SCHEMA_VERSION = "1.0"
DEFAULT_SEED = 26251

ITEMS = [
    {"item_id": f"ITEM-{i:03d}", "category": category, "unit": unit,
     "criticality": criticality, "base_daily_demand": demand}
    for i, (category, unit, criticality, demand) in enumerate([
        ("food", "pack", "high", 16), ("water", "litre", "high", 30),
        ("medical", "kit", "high", 3), ("batteries", "unit", "medium", 7),
        ("repair", "part", "medium", 4), ("shelter", "unit", "medium", 2),
        ("fuel_simulated", "litre", "high", 20), ("hygiene", "pack", "low", 5),
    ], start=1)
]

# Fictional grid coordinates; these are not real facilities or routes.
LOCATIONS = [
    {"location_id": f"LOC-{i:02d}", "location_name": name,
     "x": x, "y": y, "location_type": location_type}
    for i, (name, x, y, location_type) in enumerate([
        ("Fictional Hub A", 0, 0, "hub"),
        ("Fictional Point B", 4, 2, "demand_point"),
        ("Fictional Point C", 2, 6, "demand_point"),
        ("Fictional Point D", 8, 3, "demand_point"),
        ("Fictional Point E", 7, 8, "demand_point"),
        ("Fictional Point F", 11, 6, "demand_point"),
    ], start=1)
]


def _write_csv(path: Path, rows: List[Dict[str, object]]) -> int:
    """Write rows with a stable column order and UTF-8 encoding."""
    if not rows:
        raise ValueError(f"Refusing to write an empty dataset: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def generate_dataset(
    output_dir: str | Path,
    seed: int = DEFAULT_SEED,
    historical_days: int = 90,
    forecast_days: int = 14,
) -> dict:
    """Generate reproducible CSV files and a manifest in the output directory.

    demand_history.csv contains only the historical period. Future-period
    demand is isolated in evaluation_ground_truth.csv for evaluation only.
    """
    if historical_days < 1:
        raise ValueError("historical_days must be at least 1")
    if forecast_days < 1:
        raise ValueError("forecast_days must be at least 1")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    start = date(2025, 1, 1)
    historical_dates = [start + timedelta(days=i) for i in range(historical_days)]
    evaluation_dates = [
        start + timedelta(days=historical_days + i) for i in range(forecast_days)
    ]

    items = [
        {key: value for key, value in item.items() if key != "base_daily_demand"}
        for item in ITEMS
    ]
    _write_csv(output / "items.csv", items)
    _write_csv(output / "locations.csv", LOCATIONS)

    demand_rows: List[Dict[str, object]] = []
    ground_truth_rows: List[Dict[str, object]] = []
    inventory_rows: List[Dict[str, object]] = []
    event_number = 1
    location_factors = {
        location["location_id"]: rng.uniform(0.75, 1.35) for location in LOCATIONS
    }
    item_factors = {
        item["item_id"]: rng.uniform(0.85, 1.15) for item in ITEMS
    }

    def simulated_demand(day: date, location_id: str, item: dict) -> int:
        # A deterministic weekday effect plus seeded noise creates a useful
        # but intentionally simple forecasting baseline.
        weekday_factor = 1.15 if day.weekday() in (0, 4) else 0.9 if day.weekday() == 6 else 1.0
        expected = (
            item["base_daily_demand"]
            * location_factors[location_id]
            * item_factors[item["item_id"]]
            * weekday_factor
        )
        return max(0, round(rng.gauss(expected, max(1.0, expected * 0.12))))

    for location in LOCATIONS:
        location_id = location["location_id"]
        for item in ITEMS:
            item_id = item["item_id"]
            inventory_rows.append({
                "event_id": f"EVT-{event_number:07d}",
                "event_date": historical_dates[0].isoformat(),
                "location_id": location_id,
                "item_id": item_id,
                "event_type": "OPENING_BALANCE",
                "quantity": rng.randint(20, 250),
            })
            event_number += 1

            for day_index, day in enumerate(historical_dates):
                demand = simulated_demand(day, location_id, item)
                demand_rows.append({
                    "date": day.isoformat(),
                    "location_id": location_id,
                    "item_id": item_id,
                    "demand_units": demand,
                })
                inventory_rows.append({
                    "event_id": f"EVT-{event_number:07d}",
                    "event_date": day.isoformat(),
                    "location_id": location_id,
                    "item_id": item_id,
                    "event_type": "ISSUE",
                    "quantity": demand,
                })
                event_number += 1
                if day_index > 0 and day_index % 7 == 0:
                    receipt = max(1, demand * rng.randint(3, 8))
                    inventory_rows.append({
                        "event_id": f"EVT-{event_number:07d}",
                        "event_date": day.isoformat(),
                        "location_id": location_id,
                        "item_id": item_id,
                        "event_type": "RECEIPT",
                        "quantity": receipt,
                    })
                    event_number += 1

            for day in evaluation_dates:
                ground_truth_rows.append({
                    "date": day.isoformat(),
                    "location_id": location_id,
                    "item_id": item_id,
                    "actual_demand_units": simulated_demand(day, location_id, item),
                })

    counts = {
        "items.csv": _write_csv(output / "items.csv", items),
        "locations.csv": _write_csv(output / "locations.csv", LOCATIONS),
        "inventory_events.csv": _write_csv(output / "inventory_events.csv", inventory_rows),
        "demand_history.csv": _write_csv(output / "demand_history.csv", demand_rows),
        "evaluation_ground_truth.csv": _write_csv(
            output / "evaluation_ground_truth.csv", ground_truth_rows
        ),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "synthetic_data_only": True,
        "fictional_locations_only": True,
        "algorithm_visible_files": [
            "items.csv", "locations.csv", "inventory_events.csv", "demand_history.csv"
        ],
        "evaluation_only_files": ["evaluation_ground_truth.csv"],
        "historical_start": historical_dates[0].isoformat(),
        "historical_end": historical_dates[-1].isoformat(),
        "evaluation_start": evaluation_dates[0].isoformat(),
        "evaluation_end": evaluation_dates[-1].isoformat(),
        "row_counts": counts,
        "warning": (
            "Keep evaluation_ground_truth.csv isolated from model training and "
            "planning inputs. All entities and values are fictional."
        ),
    }
    (output / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
