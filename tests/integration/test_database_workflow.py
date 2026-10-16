from psrs.services.database import import_algorithm_inputs, read_demand, read_inventory_events
from psrs.services.demand_forecasting import forecast_demand
from psrs.services.inventory_reconciliation import reconcile_inventory
from psrs.services.synthetic_data import generate_dataset

def test_generated_inputs_import_reconcile_and_forecast_without_ground_truth(tmp_path):
    data = tmp_path / "data"
    generate_dataset(data, seed=26251, historical_days=30, forecast_days=7)
    (data / "evaluation_ground_truth.csv").unlink()
    db = tmp_path / "psrs.sqlite3"
    import_algorithm_inputs(db, data)
    demand, events = read_demand(db), read_inventory_events(db)
    forecast = forecast_demand(demand, "LOC-01", "ITEM-001", 7)
    assert len(forecast.predictions) == 7
    assert reconcile_inventory(events)
    assert all(value >= 0 for value in forecast.predictions)
