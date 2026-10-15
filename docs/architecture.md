# Architecture Notes

Phase 1 establishes a thin root-level Flask entry point and the psrs application package. Domain logic belongs in service modules, not in route handlers or templates.

Planned layers:
1. Synthetic data generation, validation, and persistence.
2. Inventory reconciliation.
3. Demand forecasting.
4. GIS and routing.
5. Scenario simulation and candidate-plan evaluation.
6. Flask presentation.
7. Automated quality checks.

Each module should define input/output contracts and be independently testable. Evaluation-only ground truth must remain isolated from forecasting and planning inputs.
