import csv
from pathlib import Path
from psrs.services.planning_workflow import build_planning_report
from psrs.services.synthetic_data import generate_dataset
from psrs.services.gis_routing import load_graph

def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def test_integrated_workflow_returns_nominal_and_adverse_scenarios(tmp_path):
    data=tmp_path/"generated"
    generate_dataset(data,seed=26251,historical_days=30,forecast_days=7)
    demand=read_rows(data/"demand_history.csv")
    events=read_rows(data/"inventory_events.csv")
    root=Path(__file__).resolve().parents[2]
    graph=load_graph(root/"data"/"synthetic"/"road_network.geojson")
    report=build_planning_report(demand_rows=demand,inventory_events=events,road_graph=graph,
        location_id="LOC-01",item_id="ITEM-001",origin="LOC-01",destination="LOC-04",
        horizon=7,capacity_limit=100)
    assert report["human_review_required"] is True
    assert [s["scenario"] for s in report["scenarios"]]==["nominal","adverse_synthetic"]
    for scenario in report["scenarios"]:
        assert scenario["candidate_plan"]["evaluation"]["capacity_used"] <= 100
        assert len(scenario["simulation"]) > 0
