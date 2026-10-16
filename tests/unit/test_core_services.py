import json

from psrs.services.demand_forecasting import forecast_demand
from psrs.services.gis_routing import calculate_route, load_graph
from psrs.services.inventory_reconciliation import reconcile_inventory
from psrs.services.plan_evaluation import evaluate_plan
from psrs.services.scenario_simulation import simulate_inventory


def test_reconciliation_ignores_duplicate_and_reports_invalid_event():
    events = [
        {"event_id": "1", "event_date": "2025-01-01", "location_id": "L", "item_id": "I",
         "event_type": "OPENING_BALANCE", "quantity": "10"},
        {"event_id": "2", "event_date": "2025-01-02", "location_id": "L", "item_id": "I",
         "event_type": "RECEIPT", "quantity": "5"},
        {"event_id": "3", "event_date": "2025-01-03", "location_id": "L", "item_id": "I",
         "event_type": "ISSUE", "quantity": "4"},
        {"event_id": "3", "event_date": "2025-01-03", "location_id": "L", "item_id": "I",
         "event_type": "ISSUE", "quantity": "4"},
        {"event_id": "4", "event_date": "2025-01-04", "location_id": "L", "item_id": "I",
         "event_type": "ISSUE", "quantity": "-2"},
    ]
    result = reconcile_inventory(events)[0]
    assert result.estimated_stock == 11
    assert result.duplicate_event_ids == ("3",)
    assert result.invalid_event_ids == ("4",)


def test_forecast_is_nonnegative_and_returns_requested_horizon():
    rows = [
        {"date": f"2025-01-{day:02d}", "location_id": "L", "item_id": "I",
         "demand_units": str(day)}
        for day in range(1, 16)
    ]
    result = forecast_demand(rows, "L", "I", horizon=4)
    assert len(result.predictions) == 4
    assert all(value >= 0 for value in result.predictions)


def test_routing_reports_connected_and_unreachable_destinations(tmp_path):
    network = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"type": "node", "node_id": "A"},
             "geometry": {"type": "Point", "coordinates": [0, 0]}},
            {"type": "Feature", "properties": {"type": "node", "node_id": "B"},
             "geometry": {"type": "Point", "coordinates": [1, 1]}},
            {"type": "Feature", "properties": {"type": "node", "node_id": "C"},
             "geometry": {"type": "Point", "coordinates": [9, 9]}},
            {"type": "Feature", "properties": {"type": "edge", "from": "A", "to": "B",
             "distance": 2, "travel_time": 3}, "geometry": None},
        ],
    }
    path = tmp_path / "network.geojson"
    path.write_text(json.dumps(network), encoding="utf-8")
    graph = load_graph(path)
    assert calculate_route(graph, "A", "B").distance == 2
    assert calculate_route(graph, "A", "C").reason == "unreachable"


def test_simulation_applies_delivery_delay_and_tracks_shortage():
    result = simulate_inventory(2, [3, 3], [{"day": 0, "quantity": 3}], delay_days=1)
    assert result.fulfilled_demand == 5
    assert result.unmet_demand == 1
    assert result.delayed_deliveries == 1


def test_plan_evaluation_rejects_capacity_violation():
    result = evaluate_plan(
        unmet_demand=0,
        distance=10,
        deliveries=[{"quantity": 8}],
        capacity_limit=5,
    )
    assert result.feasible is False
    assert "shared_transport_capacity_exceeded" in result.violations
