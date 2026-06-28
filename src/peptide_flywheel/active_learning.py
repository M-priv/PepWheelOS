from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Iterable

from pydantic import BaseModel, Field

from .dag import ResearchDAG
from .models import PeptideCandidate
from .prompt_pipeline import PromptPacket
from .scoring import heuristic_manufacturability_score


class ActiveLearningScoringSummaryOutput(BaseModel):
    run_id: str
    campaign_id: str
    selected_candidate_ids: list[str] = Field(default_factory=list)
    score_drivers: list[str] = Field(default_factory=list)
    liability_themes: list[str] = Field(default_factory=list)
    recommended_next_round: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


@dataclass
class ActiveLearningRankedCandidate:
    candidate_id: str
    rank: int
    selected: bool
    priority_score: float
    manufacturability_score: float
    exploration_score: float
    uncertainty_score: float
    risk_penalty: float
    risk_flags: list[str]
    rationale: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "rank": self.rank,
            "selected": self.selected,
            "priority_score": self.priority_score,
            "manufacturability_score": self.manufacturability_score,
            "exploration_score": self.exploration_score,
            "uncertainty_score": self.uncertainty_score,
            "risk_penalty": self.risk_penalty,
            "risk_flags": self.risk_flags,
            "rationale": self.rationale,
            "next_action": self.next_action,
        }


@dataclass
class ActiveLearningSimulationResult:
    rankings: list[ActiveLearningRankedCandidate]
    selected_candidate_ids: list[str]
    plan: dict[str, Any]
    prompt_packet: PromptPacket
    dag: ResearchDAG
    output_dir: Path
    report_path: Path
    plan_path: Path
    rankings_path: Path
    prompt_path: Path
    summary_markdown: str


def _sequence_fingerprint(sequence: str, k: int = 3) -> set[str]:
    normalized = sequence.upper().strip()
    if len(normalized) < k:
        return set(normalized)
    return {normalized[index : index + k] for index in range(0, len(normalized) - k + 1)}


def _sequence_similarity(left: str, right: str) -> float:
    left_fp = _sequence_fingerprint(left)
    right_fp = _sequence_fingerprint(right)
    if not left_fp and not right_fp:
        return 1.0
    if not left_fp or not right_fp:
        return 0.0
    return len(left_fp & right_fp) / len(left_fp | right_fp)


def _novelty_score(sequence: str, reference_sequences: list[str]) -> float:
    if not reference_sequences:
        return 100.0
    most_similar = max(_sequence_similarity(sequence, reference) for reference in reference_sequences)
    return round((1.0 - most_similar) * 100.0, 3)


def _uncertainty_score(manufacturability_score: float, risk_flags: list[str]) -> float:
    boundary_score = max(0.0, 100.0 - abs(manufacturability_score - 70.0) * 2.0)
    flag_bonus = min(15.0, len(risk_flags) * 5.0)
    return round(min(100.0, boundary_score + flag_bonus), 3)


def _risk_penalty(risk_flags: list[str]) -> float:
    return float(min(35, len(risk_flags) * 7))


def _score_candidate(
    candidate: PeptideCandidate,
    *,
    reference_sequences: list[str],
    exploitation_weight: float,
    exploration_weight: float,
    uncertainty_weight: float,
) -> dict[str, Any]:
    score = heuristic_manufacturability_score(candidate.sequence, candidate.modality.value)
    manufacturability_score = (
        float(candidate.manufacturability_score)
        if candidate.manufacturability_score is not None
        else score.overall_score
    )
    risk_flags = list(dict.fromkeys([*candidate.risk_flags, *score.risk_flags]))
    exploration_score = _novelty_score(candidate.sequence, reference_sequences)
    uncertainty_score = _uncertainty_score(manufacturability_score, risk_flags)
    risk_penalty = _risk_penalty(risk_flags)
    priority_score = (
        exploitation_weight * manufacturability_score
        + exploration_weight * exploration_score
        + uncertainty_weight * uncertainty_score
        - risk_penalty
    )
    return {
        "candidate_id": candidate.candidate_id,
        "priority_score": round(priority_score, 3),
        "manufacturability_score": round(manufacturability_score, 3),
        "exploration_score": exploration_score,
        "uncertainty_score": uncertainty_score,
        "risk_penalty": risk_penalty,
        "risk_flags": risk_flags,
    }


def _rationale(entry: dict[str, Any]) -> str:
    flags = entry["risk_flags"]
    if entry["selected"]:
        return (
            "Selected for next-round testing because the weighted priority score balances "
            f"manufacturability ({entry['manufacturability_score']}), diversity "
            f"({entry['exploration_score']}), and uncertainty ({entry['uncertainty_score']})."
        )
    if flags:
        return "Held as backup due to lower priority after risk penalties: " + ", ".join(flags)
    return "Held as backup because higher-ranked candidates better satisfy the current selection policy."


def _next_action(entry: dict[str, Any]) -> str:
    if entry["selected"]:
        return "Include in next active-learning batch and request scoring-summary review."
    if entry["risk_flags"]:
        return "Rework liabilities before committing synthesis or assay spend."
    return "Keep as alternate if batch capacity increases."


def _build_prompt_packet(
    *,
    campaign_id: str,
    run_id: str,
    plan: dict[str, Any],
    rankings: list[ActiveLearningRankedCandidate],
) -> PromptPacket:
    return PromptPacket(
        packet_id=f"active-learning-scoring-summary-{campaign_id}-{run_id}",
        agent="active-learning-summary",
        artifact="active_learning_scoring_summary",
        instruction=(
            "Summarize this active-learning simulation as strict JSON only. Identify the main "
            "score drivers, manufacturability liabilities, uncertainty concerns and practical "
            "next-round design actions. Do not invent wet-lab protocols."
        ),
        input_payload={
            "campaign_id": campaign_id,
            "run_id": run_id,
            "selection_policy": plan["selection_policy"],
            "selected_candidate_ids": plan["selected_candidate_ids"],
            "rankings": [ranking.to_dict() for ranking in rankings],
        },
        output_schema=ActiveLearningScoringSummaryOutput.model_json_schema(),
    )


def _build_report(
    *,
    campaign_id: str,
    run_id: str,
    plan: dict[str, Any],
    rankings: list[ActiveLearningRankedCandidate],
) -> str:
    lines = [
        "# Active-Learning Simulation",
        "",
        f"Run ID: `{run_id}`",
        f"Campaign ID: `{campaign_id}`",
        f"Candidates ranked: `{len(rankings)}`",
        f"Selected for next batch: `{len(plan['selected_candidate_ids'])}`",
        "",
        "## Selection policy",
        "",
        f"- Exploitation weight: `{plan['selection_policy']['exploitation_weight']}`",
        f"- Exploration weight: `{plan['selection_policy']['exploration_weight']}`",
        f"- Uncertainty weight: `{plan['selection_policy']['uncertainty_weight']}`",
        f"- Batch size: `{plan['selection_policy']['batch_size']}`",
        "",
        "## Next-round batch",
    ]
    if plan["next_round_batch"]:
        for item in plan["next_round_batch"]:
            lines.append(
                f"- {item['candidate_id']}: priority={item['priority_score']}, "
                f"manufacturability={item['manufacturability_score']}, "
                f"exploration={item['exploration_score']}, uncertainty={item['uncertainty_score']}"
            )
    else:
        lines.append("- No candidates selected.")

    lines.extend(["", "## Full ranking"])
    for ranking in rankings:
        selected_marker = "selected" if ranking.selected else "backup"
        flags = ", ".join(ranking.risk_flags) or "none"
        lines.append(
            f"- {ranking.rank}. {ranking.candidate_id} ({selected_marker}): "
            f"priority={ranking.priority_score}, flags={flags}"
        )

    lines.extend(
        [
            "",
            "## Prompt-driven summary packet",
            "",
            f"- Packet ID: `{plan['scoring_summary_prompt_id']}`",
            "- Output artifact: `active_learning_scoring_summary`",
        ]
    )
    return "\n".join(lines)


def run_active_learning_simulation(
    *,
    candidates: Iterable[PeptideCandidate],
    campaign_id: str,
    run_id: str,
    output_dir: str | Path,
    batch_size: int = 5,
    exploitation_weight: float = 0.55,
    exploration_weight: float = 0.30,
    uncertainty_weight: float = 0.15,
    dag: ResearchDAG | None = None,
) -> ActiveLearningSimulationResult:
    candidate_items = [candidate.model_copy(deep=True) for candidate in candidates]
    if not candidate_items:
        raise ValueError("At least one candidate is required for active-learning simulation.")
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")
    if min(exploitation_weight, exploration_weight, uncertainty_weight) < 0:
        raise ValueError("Selection weights must be non-negative.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    selected_ids: list[str] = []
    selected_sequences: list[str] = []
    selection_scores: dict[str, dict[str, Any]] = {}
    remaining = {candidate.candidate_id: candidate for candidate in candidate_items}

    while remaining and len(selected_ids) < min(batch_size, len(candidate_items)):
        scored_remaining = [
            _score_candidate(
                candidate,
                reference_sequences=selected_sequences,
                exploitation_weight=exploitation_weight,
                exploration_weight=exploration_weight,
                uncertainty_weight=uncertainty_weight,
            )
            for candidate in remaining.values()
        ]
        best = sorted(
            scored_remaining,
            key=lambda item: (-item["priority_score"], item["candidate_id"]),
        )[0]
        selected_id = best["candidate_id"]
        selected_ids.append(selected_id)
        selected_sequences.append(remaining[selected_id].sequence)
        selection_scores[selected_id] = best
        remaining.pop(selected_id)

    selected_sequence_context = [
        candidate.sequence
        for candidate in candidate_items
        if candidate.candidate_id in selected_ids
    ]
    ranked_entries: list[dict[str, Any]] = []
    for candidate in candidate_items:
        entry = selection_scores.get(candidate.candidate_id)
        if entry is None:
            entry = _score_candidate(
                candidate,
                reference_sequences=selected_sequence_context,
                exploitation_weight=exploitation_weight,
                exploration_weight=exploration_weight,
                uncertainty_weight=uncertainty_weight,
            )
        entry = dict(entry)
        entry["selected"] = candidate.candidate_id in selected_ids
        ranked_entries.append(entry)

    ranked_entries.sort(key=lambda item: (-item["selected"], -item["priority_score"], item["candidate_id"]))
    rankings: list[ActiveLearningRankedCandidate] = []
    for rank, entry in enumerate(ranked_entries, start=1):
        entry["rank"] = rank
        rankings.append(
            ActiveLearningRankedCandidate(
                candidate_id=entry["candidate_id"],
                rank=rank,
                selected=entry["selected"],
                priority_score=entry["priority_score"],
                manufacturability_score=entry["manufacturability_score"],
                exploration_score=entry["exploration_score"],
                uncertainty_score=entry["uncertainty_score"],
                risk_penalty=entry["risk_penalty"],
                risk_flags=entry["risk_flags"],
                rationale=_rationale(entry),
                next_action=_next_action(entry),
            )
        )

    plan = {
        "run_id": run_id,
        "campaign_id": campaign_id,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "created_by_node_type": "active_learning_simulator",
        "selection_policy": {
            "batch_size": batch_size,
            "exploitation_weight": exploitation_weight,
            "exploration_weight": exploration_weight,
            "uncertainty_weight": uncertainty_weight,
            "risk_penalty": "7 points per risk flag, capped at 35",
            "diversity_method": "greedy k-mer Jaccard novelty against selected sequences",
            "scoring_note": "Heuristic simulator only; not a trained efficacy model.",
        },
        "selected_candidate_ids": selected_ids,
        "next_round_batch": [
            ranking.to_dict()
            for ranking in rankings
            if ranking.selected
        ],
        "backup_candidates": [
            ranking.to_dict()
            for ranking in rankings
            if not ranking.selected
        ],
        "scoring_summary_prompt_id": f"active-learning-scoring-summary-{campaign_id}-{run_id}",
    }

    prompt_packet = _build_prompt_packet(
        campaign_id=campaign_id,
        run_id=run_id,
        plan=plan,
        rankings=rankings,
    )

    if dag is None:
        dag = ResearchDAG()
    plan_node_id = f"{campaign_id}-{run_id}-active-learning-plan"
    dag.add_node(plan_node_id, "active_learning_plan", plan)
    for candidate in candidate_items:
        dag.add_node(candidate.candidate_id, "peptide_candidate", candidate.model_dump(mode="json"))
    for ranking in rankings:
        rank_node_id = f"{campaign_id}-{run_id}-{ranking.candidate_id}-active-learning-rank"
        dag.add_node(rank_node_id, "active_learning_rank", ranking.to_dict())
        dag.add_edge(ranking.candidate_id, rank_node_id, "ranked_by")
        dag.add_edge(rank_node_id, plan_node_id, "informs")

    prompt_node_id = prompt_packet.packet_id
    dag.add_node(prompt_node_id, "prompt_packet", prompt_packet.model_dump())
    dag.add_edge(plan_node_id, prompt_node_id, "requests_summary")
    if not dag.validate_acyclic():
        raise ValueError("Research DAG failed acyclic validation after active-learning simulation.")

    rankings_path = output_path / "active_learning_rankings.json"
    plan_path = output_path / "active_learning_plan.json"
    prompt_path = output_path / "active_learning_scoring_summary_prompt.json"
    graph_path = output_path / "research_graph_active_learning.json"
    report_path = output_path / "active_learning_report.md"

    rankings_path.write_text(
        json.dumps([ranking.to_dict() for ranking in rankings], indent=2),
        encoding="utf-8",
    )
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    prompt_path.write_text(json.dumps(prompt_packet.model_dump(), indent=2), encoding="utf-8")
    graph_path.write_text(json.dumps(dag.to_dict(), indent=2), encoding="utf-8")

    summary_markdown = _build_report(
        campaign_id=campaign_id,
        run_id=run_id,
        plan=plan,
        rankings=rankings,
    )
    report_path.write_text(summary_markdown, encoding="utf-8")

    return ActiveLearningSimulationResult(
        rankings=rankings,
        selected_candidate_ids=selected_ids,
        plan=plan,
        prompt_packet=prompt_packet,
        dag=dag,
        output_dir=output_path,
        report_path=report_path,
        plan_path=plan_path,
        rankings_path=rankings_path,
        prompt_path=prompt_path,
        summary_markdown=summary_markdown,
    )
