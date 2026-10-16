# Architecture Notes

Phase 1 established a thin root-level Flask entry point and the `psrs` application package. Domain logic belongs in service modules, not in route handlers or templates.

## Planned layers

1. Synthetic data generation, validation, and persistence.
2. Inventory reconciliation.
3. Demand forecasting.
4. GIS and routing over fictional coordinates and networks.
5. Scenario simulation and candidate-plan evaluation.
6. Flask presentation.
7. Automated quality checks.

## Phase 2 implementation

- `psrs/services/synthetic_data.py` contains the deterministic dataset generator.
- `scripts/generate_synthetic_data.py` is its command-line entry point.
- The generator writes local CSV files and a JSON manifest.
- The default output directory is ignored by Git so generated data is reproducible without bloating the repository.
- Historical demand and evaluation-only future demand are stored in separate files.

## Current MVP implementation

- `inventory_reconciliation.py` reconstructs stock from valid events, ignores duplicate IDs after recording them, and reports invalid/stale evidence with explicit bounds.
- `demand_forecasting.py` validates daily series, compares a moving-average baseline with a lag-feature random-forest model, and returns non-negative forecasts.
- `gis_routing.py` loads the committed fictional GeoJSON network and calculates weighted shortest paths while reporting unreachable destinations.
- `scenario_simulation.py` applies demand, deliveries, delays, and synthetic weather factors in a defined day-by-day order.
- `plan_evaluation.py` checks hard capacity and route constraints independently from the objective score.
- `database.py` imports only algorithm-visible CSV inputs into SQLite with keys and checks; it does not read evaluation-only ground truth.
- `planning_workflow.py` composes forecasting, reconciliation, routing, simulation and plan evaluation for nominal and adverse synthetic scenarios.
- Flask exposes `/api/planning` and a dashboard action to run the composed workflow. The current candidate replenishment policy is a transparent heuristic, not an optimizer.
- The dashboard map uses Leaflet's simple-coordinate grid, avoiding any implication that fictional coordinates identify real locations.

The full A/B/C comparative logistics experiment, hidden inventory ground truth, uncertainty-calibration study, candidate-plan optimization, and final end-to-end verification remain outstanding.

Each module should define input/output contracts and be independently testable. Evaluation-only ground truth must remain isolated from forecasting and planning inputs. Future phases should add schema validation and ensure no evaluation labels are passed into candidate algorithms.
