"""Inventory ledger reconstruction with explicit conflicts and raw-balance evidence."""
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
    raw_ledger_balance: int
    estimated_stock: int
    lower_bound: int
    upper_bound: int
    duplicate_event_ids: tuple[str, ...]
    conflicting_event_ids: tuple[str, ...]
    invalid_event_ids: tuple[str, ...]
    def to_dict(self) -> dict:
        return asdict(self)

def _safe_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

def reconcile_inventory(events: Iterable[Mapping[str, object]], *, known_item_ids: set[str] | None = None,
                        known_location_ids: set[str] | None = None, as_of: date | None = None,
                        stale_after_days: int | None = None) -> list[InventoryEstimate]:
    """Identical repeated IDs are duplicates; conflicting payloads are flagged and not recounted."""
    if stale_after_days is not None and stale_after_days < 0:
        raise ValueError("stale_after_days must be non-negative")
    groups = defaultdict(lambda: {"opening": 0, "receipts": 0, "issues": 0,
        "duplicates": [], "conflicts": [], "invalid": [], "uncertainty": 0})
    seen = {}
    for raw in events:
        event_id = str(raw.get("event_id", ""))
        location_id = str(raw.get("location_id", ""))
        item_id = str(raw.get("item_id", ""))
        key = (location_id, item_id)
        signature = tuple(str(raw.get(k, "")) for k in
                          ("event_date", "location_id", "item_id", "event_type", "quantity"))
        if not event_id:
            groups[key]["invalid"].append("<missing>")
            continue
        if event_id in seen:
            previous_key, previous_signature = seen[event_id]
            target = groups[previous_key]
            if previous_signature == signature:
                target["duplicates"].append(event_id)
            else:
                target["conflicts"].append(event_id)
                target["uncertainty"] += max(0, _safe_int(raw.get("quantity")))
            continue
        seen[event_id] = (key, signature)
        group = groups[key]
        try:
            quantity = int(raw["quantity"])
            event_type = str(raw["event_type"])
            event_date = date.fromisoformat(str(raw["event_date"]))
        except (KeyError, TypeError, ValueError):
            group["invalid"].append(event_id)
            continue
        valid = quantity >= 0 and event_type in {"OPENING_BALANCE", "RECEIPT", "ISSUE"}
        valid = valid and bool(location_id) and bool(item_id)
        valid = valid and (known_item_ids is None or item_id in known_item_ids)
        valid = valid and (known_location_ids is None or location_id in known_location_ids)
        valid = valid and (as_of is None or event_date <= as_of)
        valid = valid and not (as_of is not None and stale_after_days is not None
                               and (as_of - event_date).days > stale_after_days)
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
        raw_balance = int(group["opening"] + group["receipts"] - group["issues"])
        uncertainty = int(group["uncertainty"])
        estimates.append(InventoryEstimate(
            location_id=location_id, item_id=item_id,
            opening_balance=int(group["opening"]), receipts=int(group["receipts"]),
            issues=int(group["issues"]), raw_ledger_balance=raw_balance,
            estimated_stock=max(0, raw_balance), lower_bound=max(0, raw_balance - uncertainty),
            upper_bound=max(0, raw_balance) + uncertainty,
            duplicate_event_ids=tuple(sorted(set(group["duplicates"]))) ,
            conflicting_event_ids=tuple(sorted(set(group["conflicts"]))) ,
            invalid_event_ids=tuple(sorted(set(group["invalid"])))
        ))
    return estimates
