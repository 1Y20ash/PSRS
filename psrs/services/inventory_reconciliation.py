"""Inventory ledger reconstruction and discrepancy reporting."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date
from typing import Iterable, Mapping


@dataclass(frozen=True)
class InventoryEstimate:
    location_id: str
    item_id: str
    opening_balance: int
    receipts: int
    issues: int
    estimated_stock: int
    lower_bound: int
    upper_bound: int
    duplicate_event_ids: tuple[str, ...]
    invalid_event_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def reconcile_inventory(
    events: Iterable[Mapping[str, object]],
    *,
    known_item_ids: set[str] | None = None,
    known_location_ids: set[str] | None = None,
    as_of: date | None = None,
) -> list[InventoryEstimate]:
    """Reconstruct stock without mutating source records.

    Duplicate event IDs are ignored after the first occurrence and reported.
    Invalid or future-dated events are excluded and reported as evidence gaps.
    Bounds widen only for excluded issue events; they are evidence-based
    uncertainty bounds, not calibrated confidence intervals.
    """
    groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {
            "opening": 0,
            "receipts": 0,
            "issues": 0,
            "duplicates": [],
            "invalid": [],
            "uncertainty": 0,
        }
    )
    seen: set[str] = set()
    for raw in events:
        event_id = str(raw.get("event_id", ""))
        location_id = str(raw.get("location_id", ""))
        item_id = str(raw.get("item_id", ""))
        key = (location_id, item_id)
        group = groups[key]
        if not event_id or event_id in seen:
            group["duplicates"].append(event_id or "<missing>")
            continue
        seen.add(event_id)
        try:
            quantity = int(raw["quantity"])
            event_type = str(raw["event_type"])
            event_date = date.fromisoformat(str(raw["event_date"]))
        except (KeyError, TypeError, ValueError):
            group["invalid"].append(event_id)
            continue
        valid = quantity >= 0 and event_type in {"OPENING_BALANCE", "RECEIPT", "ISSUE"}
        valid = valid and (known_item_ids is None or item_id in known_item_ids)
        valid = valid and (known_location_ids is None or location_id in known_location_ids)
        valid = valid and (as_of is None or event_date <= as_of)
        if not valid:
            group["invalid"].append(event_id)
            if event_type == "ISSUE" and quantity >= 0:
                group["uncertainty"] += quantity
            continue
        if event_type == "OPENING_BALANCE":
            group["opening"] += quantity
        elif event_type == "RECEIPT":
            group["receipts"] += quantity
        else:
            group["issues"] += quantity

    estimates = []
    for (location_id, item_id), group in sorted(groups.items()):
        stock = max(0, group["opening"] + group["receipts"] - group["issues"])
        uncertainty = int(group["uncertainty"])
        estimates.append(
            InventoryEstimate(
                location_id=location_id,
                item_id=item_id,
                opening_balance=int(group["opening"]),
                receipts=int(group["receipts"]),
                issues=int(group["issues"]),
                estimated_stock=stock,
                lower_bound=max(0, stock - uncertainty),
                upper_bound=stock + uncertainty,
                duplicate_event_ids=tuple(group["duplicates"]),
                invalid_event_ids=tuple(group["invalid"]),
            )
        )
    return estimates
