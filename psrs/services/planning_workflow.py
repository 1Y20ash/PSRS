"""End-to-end local planning workflow that composes tested PSRS services."""
from __future__ import annotations
from typing import Mapping
from psrs.services.demand_forecasting import forecast_demand
from psrs.services.inventory_reconciliation import reconcile_inventory
from psrs.services.gis_routing import calculate_route
from psrs.services.scenario_simulation import simulate_inventory
from psrs.services.plan_evaluation import evaluate_plan

def build_planning_report(*, demand_rows: list[Mapping[str, object]],
                          inventory_events: list[Mapping[str, object]],
                          road_graph, location_id: str, item_id: str,
                          origin: str, destination: str, horizon: int = 7,
                          capacity_limit: int = 100) -> dict:
    """Generate a human-reviewable plan under nominal and adverse synthetic scenarios.

    This is a transparent candidate-plan heuristic, not an optimizer. The adverse
    scenario uses the lower inventory bound, a synthetic 1.25 demand factor, and
    one day of delivery delay. No ground-truth file is accepted by this interface.
    """
    if capacity_limit < 0:
        raise ValueError("capacity_limit must be non-negative")
    forecast = forecast_demand(demand_rows, location_id, item_id, horizon, "auto")
    estimates = reconcile_inventory(inventory_events)
    matching = [row for row in estimates if row.location_id == location_id and row.item_id == item_id]
    if not matching:
        raise ValueError("No reconciled inventory exists for the selected location and item")
    inventory = matching[0]
    forecast_demand_units = [max(0, int(round(value))) for value in forecast.predictions]
    route = calculate_route(road_graph, origin, destination)
    scenarios = []
    for name, stock, delay, weather_factor in (
        ("nominal", inventory.estimated_stock, 0, 1.0),
        ("adverse_synthetic", inventory.lower_bound, 1, 1.25),
    ):
        target = sum(forecast_demand_units)
        requested = max(0, target - stock)
        delivery_quantity = min(requested, capacity_limit) if route.feasible else 0
        delivery = [{"day": 0, "quantity": delivery_quantity}] if delivery_quantity else []
        simulation = simulate_inventory(stock, forecast_demand_units, delivery,
                                        delay_days=delay, weather_factor=weather_factor)
        route_for_scenario = calculate_route(road_graph, origin, destination, weather_factor)
        evaluation = evaluate_plan(
            unmet_demand=simulation.unmet_demand,
            distance=route_for_scenario.distance or 0.0,
            deliveries=[{"quantity": delivery_quantity}],
            capacity_limit=capacity_limit,
            route_feasible=route_for_scenario.feasible,
        )
        scenarios.append({
            "scenario": name,
            "assumptions": {"initial_stock": stock, "delivery_delay_days": delay,
                            "synthetic_weather_demand_factor": weather_factor,
                            "transport_capacity_limit": capacity_limit},
            "simulation": simulation.to_dict(),
            "route": route_for_scenario.to_dict(),
            "candidate_plan": {"delivery_quantity": delivery_quantity,
                               "requested_quantity": requested,
                               "evaluation": evaluation.to_dict()},
        })
    return {
        "scope": "synthetic decision support; heuristic candidate, not an optimizer",
        "human_review_required": True,
        "forecast": forecast.to_dict(),
        "inventory": inventory.to_dict(),
        "scenarios": scenarios,
    }
