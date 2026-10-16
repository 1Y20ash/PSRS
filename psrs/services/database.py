"""SQLite persistence for validated synthetic inputs and planning results."""
from __future__ import annotations
import csv
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS items (item_id TEXT PRIMARY KEY, category TEXT NOT NULL, unit TEXT NOT NULL, criticality TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS locations (location_id TEXT PRIMARY KEY, location_name TEXT NOT NULL, x REAL NOT NULL, y REAL NOT NULL, location_type TEXT NOT NULL, CHECK(x BETWEEN -180 AND 180), CHECK(y BETWEEN -90 AND 90));
CREATE TABLE IF NOT EXISTS inventory_events (event_id TEXT PRIMARY KEY, event_date TEXT NOT NULL, location_id TEXT NOT NULL REFERENCES locations(location_id), item_id TEXT NOT NULL REFERENCES items(item_id), event_type TEXT NOT NULL CHECK(event_type IN ('OPENING_BALANCE','RECEIPT','ISSUE')), quantity INTEGER NOT NULL CHECK(quantity >= 0));
CREATE TABLE IF NOT EXISTS demand_history (location_id TEXT NOT NULL REFERENCES locations(location_id), item_id TEXT NOT NULL REFERENCES items(item_id), date TEXT NOT NULL, demand_units INTEGER NOT NULL CHECK(demand_units >= 0), PRIMARY KEY(location_id,item_id,date));
CREATE TABLE IF NOT EXISTS planning_results (result_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, scenario_json TEXT NOT NULL, result_json TEXT NOT NULL);
"""
def connect(database_path: str | Path) -> sqlite3.Connection:
    path=Path(database_path); path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row; db.execute("PRAGMA foreign_keys=ON"); db.executescript(SCHEMA)
    return db
def _rows(root: Path, name: str):
    path=root/name
    if not path.exists(): raise FileNotFoundError("Required synthetic input is missing: "+name)
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))
def import_algorithm_inputs(database_path: str | Path, data_dir: str | Path) -> dict[str,int]:
    """Import only algorithm-visible files; evaluation ground truth is never opened."""
    root=Path(data_dir); items=_rows(root,"items.csv"); locations=_rows(root,"locations.csv")
    events=_rows(root,"inventory_events.csv"); demand=_rows(root,"demand_history.csv")
    with connect(database_path) as db:
        db.executemany("INSERT INTO items VALUES(?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET category=excluded.category,unit=excluded.unit,criticality=excluded.criticality",
            [(r["item_id"],r["category"],r["unit"],r["criticality"]) for r in items])
        db.executemany("INSERT INTO locations VALUES(?,?,?,?,?) ON CONFLICT(location_id) DO UPDATE SET location_name=excluded.location_name,x=excluded.x,y=excluded.y,location_type=excluded.location_type",
            [(r["location_id"],r["location_name"],float(r["x"]),float(r["y"]),r["location_type"]) for r in locations])
        db.executemany("INSERT INTO inventory_events VALUES(?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET event_date=excluded.event_date,location_id=excluded.location_id,item_id=excluded.item_id,event_type=excluded.event_type,quantity=excluded.quantity",
            [(r["event_id"],r["event_date"],r["location_id"],r["item_id"],r["event_type"],int(r["quantity"])) for r in events])
        db.executemany("INSERT INTO demand_history VALUES(?,?,?,?) ON CONFLICT(location_id,item_id,date) DO UPDATE SET demand_units=excluded.demand_units",
            [(r["location_id"],r["item_id"],r["date"],int(r["demand_units"])) for r in demand])
    return {"items":len(items),"locations":len(locations),"inventory_events":len(events),"demand_rows":len(demand)}
def read_demand(database_path: str | Path) -> list[dict]:
    with connect(database_path) as db:
        return [dict(r) for r in db.execute("SELECT date,location_id,item_id,demand_units FROM demand_history ORDER BY date")]
def read_inventory_events(database_path: str | Path) -> list[dict]:
    with connect(database_path) as db:
        return [dict(r) for r in db.execute("SELECT event_id,event_date,location_id,item_id,event_type,quantity FROM inventory_events ORDER BY event_date,event_id")]
