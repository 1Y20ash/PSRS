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

Each module should define input/output contracts and be independently testable. Evaluation-only ground truth must remain isolated from forecasting and planning inputs. Future phases should add schema validation and ensure no evaluation labels are passed into candidate algorithms.
