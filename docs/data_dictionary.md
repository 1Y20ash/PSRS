# Data Dictionary

Phase 2 implements a reproducible synthetic dataset generator. Every record is fictional; location coordinates are arbitrary grid coordinates and must not be interpreted as real geography or routes.

## Generated files

All generated files are written to a local output directory (default: `data/generated/`) and are excluded from version control by default.

### items.csv

| Field | Meaning |
|---|---|
| item_id | Stable synthetic identifier |
| category | Fictional supply category |
| unit | Unit used for counts |
| criticality | Synthetic priority: low, medium, or high |

### locations.csv

| Field | Meaning |
|---|---|
| location_id | Stable synthetic identifier |
| location_name | Explicitly fictional label |
| x, y | Arbitrary integer grid coordinates |
| location_type | Hub or demand point |

### inventory_events.csv

| Field | Meaning |
|---|---|
| event_id | Unique synthetic event identifier |
| event_date | ISO date |
| location_id, item_id | References to generated dimensions |
| event_type | OPENING_BALANCE, ISSUE, or RECEIPT |
| quantity | Non-negative quantity; event type conveys the direction |

This is a starter event ledger for later reconciliation work, not a validated real-world inventory model.

### demand_history.csv

| Field | Meaning |
|---|---|
| date | Historical ISO date |
| location_id, item_id | Synthetic demand series key |
| demand_units | Non-negative observed historical demand |

### evaluation_ground_truth.csv — evaluation only

| Field | Meaning |
|---|---|
| date | Future ISO date after the historical period |
| location_id, item_id | Synthetic demand series key |
| actual_demand_units | Synthetic future actual demand, for scoring only |

The evaluation dates do not overlap the historical dates. Do not use this file as an algorithm input, training feature, or planning signal. It is only opened after predictions/plans for those dates have been produced.

### dataset_manifest.json

Records schema version, random seed, historical and evaluation date boundaries, row counts, file-access classification, and a warning about ground-truth isolation.

## Reproducibility and validation

- The generator uses Python's seeded `random.Random`; equal seeds and arguments produce byte-identical outputs.
- Defaults: seed 26251, 90 historical days, 14 evaluation days.
- Empty or negative time windows are rejected.
- Generated quantities are non-negative integers.
- The unit tests verify determinism, expected row counts, non-overlapping time windows, and the separation of evaluation truth from historical inputs.

## Explicitly not implemented yet

Road edges, vehicles, deliveries, weather/disruption scenarios, forecast outputs, and planning scenarios remain future work. Do not treat the starter inventory ledger as a full stock reconciliation system.
