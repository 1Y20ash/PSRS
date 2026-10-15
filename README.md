# PSRS — Predictive Supply Resilience System

**Problem Statement:** PS 26251 — Indian Army: Predictive Logistics & Forward Supply Chain  
**Status:** Phase 1 foundation; domain features and validation are pending.

PSRS is a proposed decision-support prototype for studying demand forecasting, inventory reconciliation, fictional GIS routing, synthetic disruption scenarios, and constraint-aware replenishment planning.

Development uses synthetic data and fictional locations only. Do not add real military logistics, routes, inventories, schedules, or other operational information. This prototype is not defence-grade certified and is not intended for real operational deployment.

## Phase 1 includes

- Flask application factory and local entry point.
- Environment-based configuration and logging.
- Placeholder dashboard and health endpoint.
- Initial pytest smoke tests.
- GitHub Actions test workflow.
- Architecture, data dictionary, experimental design, and evaluation-reporting notes.

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

## Run locally

```bash
python app.py
```

- Dashboard: http://127.0.0.1:5000/
- Health check: http://127.0.0.1:5000/health

## Tests

```bash
pytest -q
```

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
│   ├── __init__.py
│   ├── services/
│   ├── templates/
│   └── static/
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

- [x] Repository initialized
- [x] Phase 1 scaffold authored on `phase/1-repository-environment`
- [ ] Local tests verified
- [ ] GitHub Actions run verified
- [ ] Phase 1 review and pull request
