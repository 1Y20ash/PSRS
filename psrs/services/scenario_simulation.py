"""Deterministic stock simulation with explicit event ordering and validation."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
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

def simulate_inventory(initial_stock: int, daily_demand: list[int],
                       deliveries: list[Mapping[str, int]] | None = None, *,
                       delay_days: int = 0, weather_factor: float = 1.0) -> SimulationResult:
    if isinstance(initial_stock, bool) or initial_stock < 0 or delay_days < 0:
        raise ValueError("initial_stock and delay_days must be non-negative")
    if not math.isfinite(float(weather_factor)) or weather_factor < 1.0 or weather_factor > 10.0:
        raise ValueError("weather_factor must be finite and between 1 and 10")
    schedule, delayed = {}, 0
    for delivery in deliveries or []:
        day, quantity = int(delivery["day"]), int(delivery["quantity"])
        if day < 0 or quantity < 0:
            raise ValueError("delivery day and quantity must be non-negative")
        effective_day = day + delay_days
        schedule[effective_day] = schedule.get(effective_day, 0) + quantity
        delayed += int(delay_days > 0 and quantity > 0)
    stock = initial_stock
    fulfilled = unmet = shortage_days = adjusted_total = 0
    for day, raw_demand in enumerate(daily_demand):
        if isinstance(raw_demand, bool) or int(raw_demand) != raw_demand or raw_demand < 0:
            raise ValueError("daily demand must contain non-negative integers")
        # Delivery arrival occurs at the start of a day, before demand is served.
        stock += schedule.get(day, 0)
        demand = int(round(raw_demand * weather_factor))
        adjusted_total += demand
        served = min(stock, demand)
        stock -= served
        fulfilled += served
        unmet += demand - served
        shortage_days += int(demand > served)
    return SimulationResult(len(daily_demand), adjusted_total, fulfilled, unmet,
                            stock, shortage_days, delayed, weather_factor)
