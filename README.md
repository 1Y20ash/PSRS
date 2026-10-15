# PSRS — Predictive Supply Resilience System

**Problem Statement:** PS 26251 — Indian Army: Predictive Logistics & Forward Supply Chain  
**Status:** Phase 2 — reproducible synthetic dataset generator; forecasting and planning features remain pending.

PSRS is a research prototype for studying demand forecasting, inventory reconciliation, fictional GIS routing, synthetic disruption scenarios, and constraint-aware replenishment planning.

Development uses synthetic data and fictional locations only. Do not add real military logistics, routes, inventories, schedules, or other operational information. This prototype is not defence-grade certified and is not intended for real operational deployment.

## Phase 1 — repository foundation

- Flask application factory and local entry point.
- Environment-based configuration and logging.
- Placeholder dashboard and health endpoint.
- Pytest smoke tests and GitHub Actions CI.
- Architecture, data dictionary, experimental design, and evaluation-reporting notes.

## Phase 2 — synthetic data

The data generator creates reproducible CSV files from a seed. It currently defines 8 fictional item types and 6 fictional grid locations, with historical demand, inventory events, and a future evaluation window.

### Generate the dataset

Run from the repository root after installing requirements:

```bash
python scripts/generate_synthetic_data.py
```

By default, files are written to the ignored local folder `data/generated/`. You can choose a seed and time-window sizes:

```bash
python scripts/generate_synthetic_data.py --seed 26251 --historical-days 90 --forecast-days 14
python scripts/generate_synthetic_data.py --output data/generated-demo --seed 7
```

Generated files:

| File | Purpose |
|---|---|
| `items.csv` | Fictional item categories, units, and criticality |
| `locations.csv` | Fictional location names and grid coordinates |
| `inventory_events.csv` | Opening-balance, issue, and receipt events |
| `demand_history.csv` | Historical demand available to algorithms |
| `evaluation_ground_truth.csv` | Future actual demand reserved for evaluation only |
| `dataset_manifest.json` | Seed, date split, row counts, schema version, and isolation warning |

**No leakage:** `evaluation_ground_truth.csv` is intentionally separate from algorithm-visible files. Do not load it during training, forecasting, or planning. Use it only after a candidate has produced predictions or plans for the evaluation dates.

The same seed and arguments produce byte-identical files. Generated datasets are not committed by default; rerun the generator when needed.

## Requirements

- Python 3.10 or newer
- Git

## Setup — Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Setup — macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## Run the web app

```bash
python app.py
```

- Dashboard: http://127.0.0.1:5000/
- Health check: http://127.0.0.1:5000/health

## Tests

```bash
python -m pytest -q
```

CI installs dependencies from `requirements.txt` and runs the full test suite on pull requests and pushes.

## Project structure

```text
PSRS/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── psrs/
│   ├── services/
│   │   └── synthetic_data.py
│   ├── templates/
│   └── static/
├── scripts/
│   └── generate_synthetic_data.py
├── data/synthetic/
├── models/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── end_to_end/
├── docs/
└── .github/workflows/tests.yml
```

The application package is named `psrs` so the root-level `app.py` entry point does not conflict with a same-named `app/` Python package.

## Data and security rules

- Use synthetic data and fictional locations only.
- Keep secrets and local configuration in an untracked `.env` file.
- Do not commit local databases, generated datasets, or trained artifacts by default.
- The secret in `.env.example` is a placeholder, not a production secret.
- The application is a research prototype and has no defence-grade certification.

## Phase status

- [x] Phase 1 repository and CI foundation merged
- [x] Phase 2 reproducible synthetic data generator implemented on its feature branch
- [ ] Phase 2 CI verification and review
- [ ] Inventory reconciliation
- [ ] Demand forecasting
- [ ] Scenario simulation and planning
