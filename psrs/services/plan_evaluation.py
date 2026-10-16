"""Hard-constraint checks and explainable candidate-plan scoring."""
from __future__ import annotations
import math
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

def evaluate_plan(*, unmet_demand: int, distance: float,
                  deliveries: list[Mapping[str, int]], capacity_limit: int,
                  route_feasible: bool = True) -> PlanEvaluation:
    if isinstance(unmet_demand, bool) or unmet_demand < 0:
        raise ValueError("unmet_demand must be a non-negative integer")
    if isinstance(capacity_limit, bool) or capacity_limit < 0:
        raise ValueError("capacity_limit must be a non-negative integer")
    if not math.isfinite(float(distance)) or distance < 0:
        raise ValueError("distance must be finite and non-negative")
    quantities = [int(row["quantity"]) for row in deliveries]
    if any(q < 0 for q in quantities):
        raise ValueError("delivery quantities must be non-negative")
    capacity_used = sum(quantities)
    violations = []
    if capacity_used > capacity_limit:
        violations.append("shared_transport_capacity_exceeded")
    if not route_feasible:
        violations.append("route_unreachable")
    feasible = not violations
    # Transparent illustrative score; hard constraints are never traded away for score.
    score = float(unmet_demand * 100 + distance + capacity_used * 0.1)
    explanation = [f"unmet_demand={unmet_demand}", f"route_distance={distance:.3f}",
                   f"capacity={capacity_used}/{capacity_limit}"]
    explanation.append(("accepted: all hard constraints satisfied" if feasible
                        else "rejected: " + ", ".join(violations)))
    return PlanEvaluation(feasible, round(score, 3), unmet_demand, distance,
                          capacity_used, capacity_limit, violations, explanation)
