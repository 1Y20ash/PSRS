"""Routing over a fictional, validated road graph."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Mapping

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
    graph = nx.Graph()
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if properties.get("type") == "node":
            node_id = properties["node_id"]
            graph.add_node(node_id, x=geometry["coordinates"][0], y=geometry["coordinates"][1])
        elif properties.get("type") == "edge":
            graph.add_edge(
                properties["from"],
                properties["to"],
                distance=float(properties["distance"]),
                travel_time=float(properties.get("travel_time", properties["distance"])),
            )
    if not graph.nodes:
        raise ValueError("Road network contains no nodes")
    return graph


def calculate_route(graph: nx.Graph, origin: str, destination: str, weather_factor: float = 1.0) -> RouteResult:
    if origin not in graph or destination not in graph:
        return RouteResult(origin, destination, False, None, None, [], "unknown_node")
    if not nx.has_path(graph, origin, destination):
        return RouteResult(origin, destination, False, None, None, [], "unreachable")
    nodes = nx.shortest_path(graph, origin, destination, weight="distance")
    distance = sum(graph[a][b]["distance"] for a, b in zip(nodes, nodes[1:]))
    travel_time = sum(graph[a][b]["travel_time"] for a, b in zip(nodes, nodes[1:])) * max(1.0, weather_factor)
    return RouteResult(origin, destination, True, round(distance, 3), round(travel_time, 3), nodes)
