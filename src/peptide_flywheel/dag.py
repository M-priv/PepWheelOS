from __future__ import annotations

from typing import Any, Dict
import networkx as nx


class ResearchDAG:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

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
