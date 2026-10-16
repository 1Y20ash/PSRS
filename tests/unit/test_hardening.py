from datetime import date
import json
import pytest
from psrs.services.demand_forecasting import forecast_demand
from psrs.services.gis_routing import load_graph
from psrs.services.inventory_reconciliation import reconcile_inventory
from psrs.services.scenario_simulation import simulate_inventory
from psrs.services.plan_evaluation import evaluate_plan
from psrs.services.database import import_algorithm_inputs, read_demand, read_inventory_events
from psrs.services.synthetic_data import generate_dataset

def event(event_id, event_type, quantity, day="2025-01-01"):
    return {"event_id": event_id, "event_date": day, "location_id": "L", "item_id": "I", "event_type": event_type, "quantity": str(quantity)}

def test_conflicting_duplicate_is_not_double_counted_and_is_flagged():
    result = reconcile_inventory([event("x", "OPENING_BALANCE", 10), event("x", "OPENING_BALANCE", 100)])[0]
    assert result.raw_ledger_balance == 10
    assert result.conflicting_event_ids == ("x",)

def test_negative_raw_balance_is_preserved_and_visible():
    result = reconcile_inventory([event("o", "OPENING_BALANCE", 2), event("i", "ISSUE", 5)])[0]
    assert result.raw_ledger_balance == -3
    assert result.estimated_stock == 0

def test_forecasting_rejects_invalid_model_and_horizon():
    rows = [{"date": f"2025-01-{i:02d}", "location_id": "L", "item_id": "I", "demand_units": i} for i in range(1, 16)]
    with pytest.raises(ValueError): forecast_demand(rows, "L", "I", horizon=100)
    with pytest.raises(ValueError): forecast_demand(rows, "L", "I", model="magic")

def test_simulation_rejects_invalid_weather_and_adjusts_reported_total():
    with pytest.raises(ValueError): simulate_inventory(2, [1], weather_factor=float("nan"))
    result = simulate_inventory(10, [2, 3], weather_factor=1.5)
    assert result.total_demand == 7

def test_route_validation_rejects_invalid_weights(tmp_path):
    payload = {"type":"FeatureCollection","features":[
      {"type":"Feature","properties":{"type":"node","node_id":"A"},"geometry":{"type":"Point","coordinates":[0,0]}},
      {"type":"Feature","properties":{"type":"node","node_id":"B"},"geometry":{"type":"Point","coordinates":[1,1]}},
      {"type":"Feature","properties":{"type":"edge","from":"A","to":"B","distance":-1},"geometry":None}]}
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError): load_graph(path)

def test_sqlite_import_never_requires_ground_truth(tmp_path):
    data = tmp_path / "generated"
    generate_dataset(data, seed=10, historical_days=12, forecast_days=3)
    (data / "evaluation_ground_truth.csv").unlink()
    db = tmp_path / "psrs.sqlite3"
    result = import_algorithm_inputs(db, data)
    assert result["demand_rows"] > 0 and read_demand(db) and read_inventory_events(db)

def test_plan_constraints_are_hard():
    result = evaluate_plan(unmet_demand=2, distance=3, deliveries=[{"quantity":5}], capacity_limit=4)
    assert not result.feasible
    assert "shared_transport_capacity_exceeded" in result.violations
    with pytest.raises(ValueError): evaluate_plan(unmet_demand=-1, distance=0, deliveries=[], capacity_limit=1)
