# PSRS — Predictive Supply Resilience System

**Problem Statement:** PS 26251 — Indian Army: Predictive Logistics & Forward Supply Chain  
**Status:** Synthetic-only research prototype. Core services are being hardened; full A/B/C logistics evaluation remains pending.

PSRS studies demand forecasting, inventory reconciliation, fictional GIS routing, synthetic disruption scenarios, and constraint-aware replenishment planning. It uses fictional data only and is not defence-grade certified or intended for real operational deployment.

## Setup

Python 3.10+ is required.

Windows PowerShell:

    py -3.10 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Copy-Item .env.example .env

macOS/Linux:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    cp .env.example .env

Generate reproducible fictional data and run the application:

    python scripts/generate_synthetic_data.py --seed 26251 --historical-days 90 --forecast-days 14
    python app.py

Dashboard: http://127.0.0.1:5000/  
Health: http://127.0.0.1:5000/health

## Implemented modules

- Inventory ledger reconstruction with duplicate/conflict detection and raw negative-balance visibility.
- Moving-average baseline and lag-feature Random Forest with chronological validation, MAE and WAPE.
- GeoJSON validation and shortest-path routing over fictional locations.
- Inventory simulation with documented delivery-before-demand ordering and synthetic delay factors.
- Plan evaluation with independent hard-capacity and route-feasibility checks.
- SQLite persistence for algorithm-visible inputs.
- Flask APIs for summary, forecast, inventory, route and illustrative plan evaluation.
- Leaflet map for the fictional road graph. Online map tiles require internet; routing calculations are local.
- Unit/integration tests and GitHub Actions CI.

## Synthetic data and ground truth isolation

The generator writes items, locations, inventory events, historical demand, future evaluation ground truth, and a manifest under ignored local data directories. The database importer reads only items, locations, inventory events and historical demand; it never opens the ground-truth file. Evaluation labels may be consulted only after forecasts or plans have been generated.

## Experiments

Run a reproducible forecasting-only comparison:

    python scripts/run_experiments.py --seed 26251 --historical-days 90 --forecast-days 14

The generated local report compares baseline, ML and automatic model selection with MAE/WAPE. This does **not** complete the PDP's A/B/C integrated logistics experiment. No integrated improvement is claimed until those configurations have been implemented and evaluated on equivalent scenario inputs.

## Quality and security

    python -m pytest -q

Configure a random PSRS_SECRET_KEY before enabling session-based features. Set PSRS_COOKIE_SECURE=true behind HTTPS and PSRS_TRUSTED_HOSTS for a known deployment. Never commit .env, local databases, generated datasets or model artifacts. See docs/security.md.

All quantities, locations, routes and disruption scenarios are synthetic. Do not add real military logistics data. This prototype has no operational certification.
