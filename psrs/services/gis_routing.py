"""Validated routing over a fictional road graph."""
from __future__ import annotations
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
import networkx as nx

@dataclass(frozen=True)
class RouteResult:
    origin: str
    destination: str
    feasible: bool
    distance: float | None
    travel_time: float | None
    nodes: list[str]
    reason: str | None = None
    def to_dict(self) -> dict:
        return asdict(self)

def load_graph(geojson_path: str | Path) -> nx.Graph:
    payload = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError("Road network must be a GeoJSON FeatureCollection")
    graph = nx.Graph()
    declared_nodes, edge_records = set(), []
    for feature in payload["features"]:
        if not isinstance(feature, dict):
            raise ValueError("Every GeoJSON feature must be an object")
        properties, geometry = feature.get("properties") or {}, feature.get("geometry") or {}
        try:
            if properties.get("type") == "node":
                node_id = str(properties["node_id"])
                coords = geometry["coordinates"]
                x, y = float(coords[0]), float(coords[1])
                if not node_id or not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError
                if not (-180 <= x <= 180 and -90 <= y <= 90):
                    raise ValueError
                if node_id in declared_nodes:
                    raise ValueError("Duplicate road node")
                declared_nodes.add(node_id)
                graph.add_node(node_id, x=x, y=y)
            elif properties.get("type") == "edge":
                start, end = str(properties["from"]), str(properties["to"])
                distance = float(properties["distance"])
                travel_time = float(properties.get("travel_time", distance))
                if start == end or distance <= 0 or travel_time <= 0:
                    raise ValueError
                if not math.isfinite(distance) or not math.isfinite(travel_time):
                    raise ValueError
                edge_records.append((start, end, distance, travel_time))
        except (KeyError, TypeError, IndexError, ValueError) as exc:
            raise ValueError("Invalid road-network node or edge properties") from exc
    if not declared_nodes:
        raise ValueError("Road network contains no nodes")
    for start, end, distance, travel_time in edge_records:
        if start not in declared_nodes or end not in declared_nodes:
            raise ValueError("Road network contains an edge with an undeclared node")
        if graph.has_edge(start, end):
            raise ValueError("Road network contains a duplicate edge")
        graph.add_edge(start, end, distance=distance, travel_time=travel_time)
    return graph

def calculate_route(graph: nx.Graph, origin: str, destination: str,
                    weather_factor: float = 1.0) -> RouteResult:
    if not math.isfinite(float(weather_factor)) or weather_factor < 1.0 or weather_factor > 10.0:
        raise ValueError("weather_factor must be finite and between 1 and 10")
    if origin not in graph or destination not in graph:
        return RouteResult(origin, destination, False, None, None, [], "unknown_node")
    try:
        nodes = nx.shortest_path(graph, origin, destination, weight="distance")
    except nx.NetworkXNoPath:
        return RouteResult(origin, destination, False, None, None, [], "unreachable")
    distance = sum(graph[a][b]["distance"] for a, b in zip(nodes, nodes[1:]))
    travel_time = sum(graph[a][b]["travel_time"] for a, b in zip(nodes, nodes[1:])) * weather_factor
    return RouteResult(origin, destination, True, round(distance, 3), round(travel_time, 3), nodes)
