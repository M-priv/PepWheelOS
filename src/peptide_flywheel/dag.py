from __future__ import annotations

from typing import Any, Dict
import networkx as nx


class ResearchDAG:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ResearchDAG":
        graph = cls()
        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            raise ValueError("DAG payload missing or invalid 'nodes' list.")

        for raw_node in nodes:
            if not isinstance(raw_node, dict):
                raise ValueError("DAG payload node must be a dictionary.")
            node_id = raw_node.get("id")
            if node_id is None:
                raise ValueError("DAG payload node missing required id.")
            attrs = dict(raw_node)
            attrs.pop("id")
            graph.graph.add_node(str(node_id), **attrs)

        edges = payload.get("edges", [])
        if not isinstance(edges, list):
            raise ValueError("DAG payload 'edges' must be a list.")
        for raw_edge in edges:
            if not isinstance(raw_edge, dict):
                raise ValueError("DAG payload edge must be a dictionary.")
            source = raw_edge.get("source")
            target = raw_edge.get("target")
            if source is None or target is None:
                raise ValueError("DAG payload edge missing required source or target.")
            source_id = str(source)
            target_id = str(target)
            if source_id not in graph.graph:
                raise ValueError(f"Source node not found while loading DAG: {source_id}")
            if target_id not in graph.graph:
                raise ValueError(f"Target node not found while loading DAG: {target_id}")

            attrs = dict(raw_edge)
            attrs.pop("source", None)
            attrs.pop("target", None)
            graph.graph.add_edge(source_id, target_id, **attrs)

        return graph

    def add_node(self, node_id: str, node_type: str, payload: Dict[str, Any]) -> None:
        self.graph.add_node(node_id, node_type=node_type, payload=payload)

    def add_edge(self, source_id: str, target_id: str, edge_type: str) -> None:
        if source_id not in self.graph:
            raise ValueError(f"Source node not found: {source_id}")
        if target_id not in self.graph:
            raise ValueError(f"Target node not found: {target_id}")
        self.graph.add_edge(source_id, target_id, edge_type=edge_type)

    def ancestors(self, node_id: str):
        return nx.ancestors(self.graph, node_id)

    def descendants(self, node_id: str):
        return nx.descendants(self.graph, node_id)

    def validate_acyclic(self) -> bool:
        return nx.is_directed_acyclic_graph(self.graph)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"id": node_id, **attrs}
                for node_id, attrs in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, **attrs}
                for source, target, attrs in self.graph.edges(data=True)
            ],
        }
