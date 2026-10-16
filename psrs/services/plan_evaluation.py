"""Hard-constraint checks and explainable candidate-plan scoring."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping


@dataclass(frozen=True)
class PlanEvaluation:
    feasible: bool
    objective_score: float
    unmet_demand: int
    distance: float
    capacity_used: int
    capacity_limit: int
    violations: list[str]
    explanation: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_plan(
    *,
    unmet_demand: int,
    distance: float,
    deliveries: list[Mapping[str, int]],
    capacity_limit: int,
    route_feasible: bool = True,
) -> PlanEvaluation:
    capacity_used = sum(int(delivery["quantity"]) for delivery in deliveries)
    violations = []
    if capacity_used > capacity_limit:
        violations.append("shared_transport_capacity_exceeded")
    if not route_feasible:
        violations.append("route_unreachable")
    feasible = not violations
    score = float(unmet_demand * 100 + distance + capacity_used * 0.1)
    explanation = [
        f"unmet_demand={unmet_demand}",
        f"route_distance={distance:.3f}",
        f"capacity={capacity_used}/{capacity_limit}",
    ]
    if violations:
        explanation.append("rejected: " + ", ".join(violations))
    else:
        explanation.append("accepted: all hard constraints satisfied")
    return PlanEvaluation(feasible, round(score, 3), unmet_demand, distance,
                          capacity_used, capacity_limit, violations, explanation)
