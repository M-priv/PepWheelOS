from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class MultiObjectiveCandidate:
    candidate_id: str
    sequence: str
    objectives: Dict[str, float]  # Higher is always better (e.g. {"potency": 0.85, "manufacturability": 0.90, "solubility": 0.80})
    pareto_rank: int = 0
    crowding_distance: float = 0.0
    dominated_by_count: int = 0
    dominates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "sequence": self.sequence,
            "objectives": self.objectives,
            "pareto_rank": self.pareto_rank,
            "crowding_distance": round(self.crowding_distance, 4),
        }


def dominates(c1: MultiObjectiveCandidate, c2: MultiObjectiveCandidate) -> bool:
    """Check if candidate 1 Pareto-dominates candidate 2 (all objectives >= and at least one >)."""
    keys = c1.objectives.keys()
    at_least_one_better = False
    for k in keys:
        v1 = c1.objectives.get(k, 0.0)
        v2 = c2.objectives.get(k, 0.0)
        if v1 < v2:
            return False
        if v1 > v2:
            at_least_one_better = True
    return at_least_one_better


def fast_non_dominated_sort(candidates: List[MultiObjectiveCandidate]) -> List[List[MultiObjectiveCandidate]]:
    """NSGA-II Fast Non-Dominated Sorting algorithm.
    
    Partitions candidates into non-dominated Pareto fronts: Front 1 (Rank 1), Front 2 (Rank 2), etc.
    """
    if not candidates:
        return []

    fronts: List[List[MultiObjectiveCandidate]] = [[]]

    for p in candidates:
        p.dominates = []
        p.dominated_by_count = 0
        for q in candidates:
            if p.candidate_id == q.candidate_id:
                continue
            if dominates(p, q):
                p.dominates.append(q.candidate_id)
            elif dominates(q, p):
                p.dominated_by_count += 1

        if p.dominated_by_count == 0:
            p.pareto_rank = 1
            fronts[0].append(p)

    cand_by_id = {c.candidate_id: c for c in candidates}
    i = 0
    while len(fronts[i]) > 0:
        next_front: List[MultiObjectiveCandidate] = []
        for p in fronts[i]:
            for q_id in p.dominates:
                q = cand_by_id[q_id]
                q.dominated_by_count -= 1
                if q.dominated_by_count == 0:
                    q.pareto_rank = i + 2
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    if not fronts[-1]:
        fronts.pop()

    # Calculate crowding distances per front
    for front in fronts:
        assign_crowding_distance(front)

    return fronts


def assign_crowding_distance(front: List[MultiObjectiveCandidate]) -> None:
    """Calculate NSGA-II crowding distances to preserve diversity along the trade-off front."""
    l = len(front)
    if l == 0:
        return
    if l <= 2:
        for c in front:
            c.crowding_distance = float("inf")
        return

    for c in front:
        c.crowding_distance = 0.0

    objective_keys = list(front[0].objectives.keys())

    for obj in objective_keys:
        # Sort front by this objective
        front.sort(key=lambda c: c.objectives.get(obj, 0.0))
        min_val = front[0].objectives.get(obj, 0.0)
        max_val = front[-1].objectives.get(obj, 0.0)
        val_range = max_val - min_val

        # Boundary candidates get infinite distance
        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")

        if val_range > 0:
            for i in range(1, l - 1):
                next_val = front[i + 1].objectives.get(obj, 0.0)
                prev_val = front[i - 1].objectives.get(obj, 0.0)
                front[i].crowding_distance += (next_val - prev_val) / val_range


def select_top_pareto_candidates(
    fronts: List[List[MultiObjectiveCandidate]],
    k: int,
) -> List[MultiObjectiveCandidate]:
    """Select top k candidates prioritized by Pareto rank, then by crowding distance."""
    selected: List[MultiObjectiveCandidate] = []
    for front in fronts:
        if len(selected) + len(front) <= k:
            selected.extend(front)
        else:
            # Sort remaining front by crowding distance descending
            sorted_front = sorted(front, key=lambda c: c.crowding_distance, reverse=True)
            needed = k - len(selected)
            selected.extend(sorted_front[:needed])
            break
    return selected
