"""PSRS Flask application factory and thin API layer."""
import logging
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from config import Config
from psrs.services.logging_config import configure_logging
from psrs.services.database import import_algorithm_inputs, read_demand, read_inventory_events
from psrs.services.demand_forecasting import forecast_demand
from psrs.services.inventory_reconciliation import reconcile_inventory
from psrs.services.gis_routing import load_graph, calculate_route
from psrs.services.plan_evaluation import evaluate_plan
from psrs.services.planning_workflow import build_planning_report

logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    configure_logging()
    application = Flask(__name__, template_folder="templates", static_folder="static")
    application.config.from_object(config_class)
    application.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    if not application.config.get("SECRET_KEY"):
        logger.warning("PSRS_SECRET_KEY is unset; do not enable session-dependent features.")

    def algorithm_inputs():
        data_dir = Path(application.config["DATA_DIRECTORY"])
        if not (data_dir / "demand_history.csv").exists():
            return [], []
        try:
            import_algorithm_inputs(application.config["DATABASE_PATH"], data_dir)
            return read_demand(application.config["DATABASE_PATH"]), read_inventory_events(application.config["DATABASE_PATH"])
        except (OSError, ValueError, KeyError) as exc:
            logger.exception("Synthetic input import failed")
            raise RuntimeError("Synthetic inputs are invalid or unavailable") from exc

    def road_graph():
        return load_graph(Path(__file__).resolve().parent.parent / "data" / "synthetic" / "road_network.geojson")

    @application.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com; "
            "img-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        return response

    @application.get("/")
    def index():
        return render_template("index.html", project_name="PSRS")

    @application.get("/health")
    def health():
        # Preserve the original response contract for existing health-check clients.
        return jsonify({"status": "ok", "project": "PSRS"})

    @application.get("/api/summary")
    def summary():
        try:
            demand, inventory = algorithm_inputs()
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"dataset_available": bool(demand and inventory), "demand_rows": len(demand),
            "inventory_events": len(inventory), "locations": len({r["location_id"] for r in demand}),
            "items": len({r["item_id"] for r in demand})})

    @application.get("/api/forecast")
    def forecast():
        try:
            demand, _ = algorithm_inputs()
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 400
        if not demand:
            return jsonify({"error": "Generate a synthetic dataset before forecasting"}), 404
        try:
            horizon_arg = request.args.get("horizon", "7")
            if not horizon_arg.isdigit():
                raise ValueError("horizon must be an integer between 1 and 90")
            result = forecast_demand(demand, request.args.get("location_id", "LOC-01"),
                request.args.get("item_id", "ITEM-001"), int(horizon_arg), request.args.get("model", "auto"))
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(result.to_dict())

    @application.get("/api/inventory")
    def inventory():
        try:
            _, events = algorithm_inputs()
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 400
        if not events:
            return jsonify({"error": "Generate a synthetic dataset before reconciliation"}), 404
        return jsonify({"estimates": [r.to_dict() for r in reconcile_inventory(events)]})

    @application.get("/api/route")
    def route():
        try:
            factor = float(request.args.get("weather_factor", "1"))
            result = calculate_route(road_graph(), request.args.get("origin", "LOC-01"),
                                     request.args.get("destination", "LOC-04"), factor)
        except (ValueError, OSError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(result.to_dict())

    @application.get("/api/planning")
    def planning():
        try:
            demand, events = algorithm_inputs()
            if not demand or not events:
                return jsonify({"error": "Generate a synthetic dataset before planning"}), 404
            horizon_arg = request.args.get("horizon", "7")
            capacity_arg = request.args.get("capacity_limit", "100")
            if not horizon_arg.isdigit() or not capacity_arg.isdigit():
                raise ValueError("horizon and capacity_limit must be non-negative integers")
            report = build_planning_report(
                demand_rows=demand, inventory_events=events, road_graph=road_graph(),
                location_id=request.args.get("location_id", "LOC-01"),
                item_id=request.args.get("item_id", "ITEM-001"),
                origin=request.args.get("origin", "LOC-01"),
                destination=request.args.get("destination", "LOC-04"),
                horizon=int(horizon_arg), capacity_limit=int(capacity_arg))
        except (ValueError, OSError, TypeError, RuntimeError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(report)

    @application.get("/api/plan")
    def plan():
        try:
            unmet = request.args.get("unmet_demand", default=0, type=int)
            distance = request.args.get("distance", default=0.0, type=float)
            capacity = request.args.get("capacity_limit", default=100, type=int)
            quantity = request.args.get("quantity", default=0, type=int)
            route_result = calculate_route(road_graph(), request.args.get("origin", "LOC-01"),
                                            request.args.get("destination", "LOC-04"))
            result = evaluate_plan(unmet_demand=unmet, distance=distance if distance else (route_result.distance or 0),
                deliveries=[{"quantity": quantity}], capacity_limit=capacity, route_feasible=route_result.feasible)
        except (ValueError, OSError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"route": route_result.to_dict(), "plan": result.to_dict()})

    @application.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": "Request payload exceeds the 1 MiB limit"}), 413

    return application
