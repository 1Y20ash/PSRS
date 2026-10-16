"""Deterministic stock simulation under synthetic delivery scenarios."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping


@dataclass(frozen=True)
class SimulationResult:
    days: int
    total_demand: int
    fulfilled_demand: int
    unmet_demand: int
    ending_stock: int
    shortage_days: int
    delayed_deliveries: int
    weather_factor: float

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_inventory(
    initial_stock: int,
    daily_demand: list[int],
    deliveries: list[Mapping[str, int]] | None = None,
    *,
    delay_days: int = 0,
    weather_factor: float = 1.0,
) -> SimulationResult:
    if initial_stock < 0 or delay_days < 0:
        raise ValueError("initial_stock and delay_days must be non-negative")
    deliveries = deliveries or []
    schedule: dict[int, int] = {}
    delayed = 0
    for delivery in deliveries:
        day = int(delivery["day"])
        quantity = int(delivery["quantity"])
        if day < 0 or quantity < 0:
            raise ValueError("delivery day and quantity must be non-negative")
        effective_day = day + delay_days
        schedule[effective_day] = schedule.get(effective_day, 0) + quantity
        delayed += int(delay_days > 0)
    stock = initial_stock
    fulfilled = unmet = shortage_days = 0
    for day, demand in enumerate(daily_demand):
        if demand < 0:
            raise ValueError("daily demand must be non-negative")
        stock += schedule.get(day, 0)
        adjusted_demand = int(round(demand * max(1.0, weather_factor)))
        served = min(stock, adjusted_demand)
        stock -= served
        fulfilled += served
        unmet += adjusted_demand - served
        shortage_days += int(adjusted_demand > served)
    return SimulationResult(len(daily_demand), sum(daily_demand), fulfilled, unmet,
                            stock, shortage_days, delayed, weather_factor)
