"""PSRS application package and Flask application factory."""
import csv
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from config import Config
from psrs.services.logging_config import configure_logging
from psrs.services.demand_forecasting import forecast_demand
from psrs.services.inventory_reconciliation import reconcile_inventory


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def create_app(config_class=Config):
    configure_logging()
    application = Flask(__name__, template_folder="templates", static_folder="static")
    application.config.from_object(config_class)

    @application.get("/")
    def index():
        return render_template("index.html", project_name="PSRS")

    @application.get("/health")
    def health():
        return jsonify({"status": "ok", "project": "PSRS"})

    @application.get("/api/summary")
    def summary():
        data_dir = Path(application.config["DATA_DIRECTORY"])
        demand = _read_csv(data_dir / "demand_history.csv")
        inventory = _read_csv(data_dir / "inventory_events.csv")
        return jsonify({
            "dataset_available": bool(demand and inventory),
            "demand_rows": len(demand),
            "inventory_events": len(inventory),
            "locations": len({row["location_id"] for row in demand}),
            "items": len({row["item_id"] for row in demand}),
        })

    @application.get("/api/forecast")
    def forecast():
        data_dir = Path(application.config["DATA_DIRECTORY"])
        demand = _read_csv(data_dir / "demand_history.csv")
        location_id = request.args.get("location_id", "LOC-01")
        item_id = request.args.get("item_id", "ITEM-001")
        horizon = request.args.get("horizon", default=7, type=int)
        if not demand:
            return jsonify({"error": "Generate a synthetic dataset before forecasting"}), 404
        try:
            result = forecast_demand(demand, location_id, item_id, horizon)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(result.to_dict())

    @application.get("/api/inventory")
    def inventory():
        data_dir = Path(application.config["DATA_DIRECTORY"])
        events = _read_csv(data_dir / "inventory_events.csv")
        if not events:
            return jsonify({"error": "Generate a synthetic dataset before reconciliation"}), 404
        estimates = reconcile_inventory(events)
        return jsonify({"estimates": [estimate.to_dict() for estimate in estimates]})

    return application
