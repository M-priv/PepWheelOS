from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Iterable, List
from collections import Counter

from .dag import ResearchDAG
from .models import CandidateStatus, DecisionRecord, ExperimentalResult, PeptideCandidate
from .result_ingestion import classify_failure_modes
from .reporting import batch_summary_markdown
from .storage import append_jsonl, save_json_record


@dataclass
class ResultReviewSummary:
    candidates: List[PeptideCandidate]
    results: List[ExperimentalResult]
    decisions: List[DecisionRecord]
    recommendations: List[dict[str, Any]]
    campaign_recommendation_plan: dict[str, Any]
    campaign_decision: DecisionRecord
    next_round_plan: dict[str, Any]
    dag: ResearchDAG
    output_dir: Path
    report_path: Path
    status_transitions: List[tuple[str, CandidateStatus, CandidateStatus]]
    warnings: List[str]


def _status_from_failures(failure_modes: list[str]) -> CandidateStatus:
    if failure_modes:
        return CandidateStatus.REJECTED
    return CandidateStatus.ADVANCED


def _decision_text_from_status(status: CandidateStatus) -> str:
    if status == CandidateStatus.REJECTED:
        return "rejected"
    return "advanced"


def _format_candidate_for_dag(candidate: PeptideCandidate) -> dict:
    payload = candidate.model_dump(mode="json")
    payload["status"] = candidate.status.value
    return payload


FAILURE_RECOMMENDATIONS: dict[str, list[str]] = {
    "SYN_LOW_YIELD": [
        "Revisit synthesis chemistry and optimize equivalents/reaction conditions.",
        "Add an alternate synthetic route contingency before rerunning this sequence.",
    ],
    "SYN_LOW_CRUDE_PURITY": [
        "Improve purification design before rerun (extra polishing step or alternate resin).",
        "Benchmark impurity profile against historical route controls.",
    ],
    "SYN_HYDROPHOBIC_SEQUENCE": [
        "Review hydrophobe burden and consider polar substitutions.",
        "Run solubility-focused analog redesign before repeating synthesis.",
    ],
    "SYN_SEQUENCE_LENGTH_RISK": [
        "Consider length-optimized truncation/extension experiments.",
        "Retune design constraints to avoid out-of-distribution sequence lengths.",
    ],
    "SYN_CYCLISATION_FAILED": [
        "Reassess cyclization chemistry and protecting group strategy.",
        "Explore orthogonal cyclization chemistry for the backup route.",
    ],
    "SYN_MODIFICATION_FAILED": [
        "Verify modification reagents and orthogonal reaction order.",
        "Retry with a fallback modification route and tighter QC checks.",
    ],
    "SYN_SCALE_UP_FAILED": [
        "Prototype scale-up conditions in staged pilot batches before rerun.",
        "Split process transfer into stages to isolate bottlenecks.",
    ],
    "PURIFICATION_DIFFICULT": [
        "Design purification handles or alternative cleanup strategy before synthesis.",
        "Evaluate fast-condition screening for yield/purity tradeoffs.",
    ],
    "NO_BINDING": [
        "Recheck assay controls and replicate measurements.",
        "Revisit target engagement assumptions and add orthogonal readouts.",
    ],
    "WEAK_BINDING": [
        "Run broader concentration-response series across orthogonal assays.",
        "Prioritize analogs with improved contact surface and selectivity potential.",
    ],
    "NON_SPECIFIC_BINDING": [
        "Add counter-screening against an off-target panel.",
        "Refine design constraints for selectivity before next synthesis.",
    ],
    "OFF_TARGET_SIGNAL": [
        "Run a cleaned specificity panel before repeating synthesis.",
        "Trim motifs linked to known off-target signatures.",
    ],
    "NO_FUNCTIONAL_EFFECT": [
        "Investigate alternate functional readout and timing points.",
        "Review model system validity and control gating before repeating.",
    ],
    "ASSAY_INTERFERENCE": [
        "Re-run in orthogonal assay chemistry with strengthened controls.",
        "Collect signal-to-background and blank-corrected baseline first.",
    ],
    "LOW_AQUEOUS_SOLUBILITY": [
        "Improve assay and formulation pre-checks for solubility.",
        "Screen polar substitutions before rerunning the assay.",
    ],
    "AGGREGATION": [
        "Run pre-assay aggregation diagnostics and adjust assay format.",
        "Avoid formulation conditions that trigger rapid aggregation.",
    ],
    "AGGREGATED_PRODUCT": [
        "Check peptide handling conditions and storage before rerun.",
        "Add stabilising workflow guards (shorter hold times, chilled handling).",
    ],
    "PRECIPITATION": [
        "Investigate buffer composition and concentration envelope changes.",
        "Re-evaluate formulation conditions before next rerun.",
    ],
    "MODEL_OVERCONFIDENCE": [
        "Tighten uncertainty capture and reduce exploitation pressure.",
        "Broaden exploration before additional synthesis commitments.",
    ],
    "WRONG_BINDING_SITE": [
        "Validate binding-site assumptions before revisiting design.",
        "Add binding-site probes to next design batch.",
    ],
}


def _recommendations_for_failure_modes(
    failure_modes: list[str],
    next_status: CandidateStatus,
) -> list[str]:
    if not failure_modes:
        if next_status == CandidateStatus.ADVANCED:
            return [
                "Advance to orthogonal confirmation assays.",
                "Prioritize the candidate for synthesis and CRO handoff if not complete.",
            ]
        return ["Reconfirm interpretation and controls before rerun."]

    ordered: list[str] = []
    seen: set[str] = set()
    for mode in failure_modes:
        for recommendation in FAILURE_RECOMMENDATIONS.get(mode, ()):
            if recommendation in seen:
                continue
            ordered.append(recommendation)
            seen.add(recommendation)

    if ordered:
        return ordered
    if next_status == CandidateStatus.REJECTED:
        return ["Re-check protocol assumptions and rerun only after controls are tightened."]
    return ["Run an orthogonal assay to validate ambiguous findings."]


def _build_campaign_recommendation_plan(
    run_id: str,
    campaign_id: str,
    review_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts = Counter(item["status"] for item in review_recommendations)
    failure_mode_counts = Counter()
    for entry in review_recommendations:
        for mode in entry.get("failure_modes", []) or []:
            failure_mode_counts[str(mode)] += 1

    recommendation_counts = Counter()
    for entry in review_recommendations:
        for recommendation in entry.get("recommendations", []) or []:
            recommendation_counts[str(recommendation)] += 1

    prioritized_steps = [
        {"step": step, "count": count}
        for step, count in recommendation_counts.most_common()
    ]

    return {
        "run_id": run_id,
        "campaign_id": campaign_id,
        "candidates_reviewed": len(review_recommendations),
        "status_counts": dict(status_counts),
        "failure_mode_counts": dict(failure_mode_counts),
        "prioritized_next_steps": prioritized_steps,
        "created_by_node_type": "result_review",
    }


def _build_next_round_plan(
    run_id: str,
    campaign_id: str,
    campaign_plan: dict[str, Any],
    review_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "advance": [],
        "retest_or_remediate": [],
        "reject": [],
    }
    for item in review_recommendations:
        bucket_key = item.get("status")
        entry = {
            "candidate_id": item.get("candidate_id"),
            "decision_id": item.get("decision_id"),
            "result_id": item.get("result_id"),
            "failure_modes": item.get("failure_modes", []),
            "recommendations": item.get("recommendations", []),
        }
        if bucket_key == CandidateStatus.ADVANCED.value:
            buckets["advance"].append(entry)
        elif bucket_key == CandidateStatus.REJECTED.value:
            buckets["reject"].append(entry)
        else:
            buckets["retest_or_remediate"].append(entry)

    return {
        "run_id": run_id,
        "campaign_id": campaign_id,
        "next_round_batch": {
            "advance_for_orthogonal_confirmation": buckets["advance"],
            "retest_or_rework": buckets["retest_or_remediate"],
            "drop_from_active_pool": buckets["reject"],
        },
        "priority_focus": campaign_plan.get("prioritized_next_steps", []),
        "created_from_node_type": "campaign_recommendation_plan",
    }


def _build_campaign_decision_record(
    *,
    campaign_id: str,
    run_id: str,
    campaign_plan: dict[str, Any],
    next_round_plan: dict[str, Any],
) -> DecisionRecord:
    status_counts = campaign_plan.get("status_counts", {})
    advanced_count = int(status_counts.get(CandidateStatus.ADVANCED.value, 0))
    rejected_count = int(status_counts.get(CandidateStatus.REJECTED.value, 0))
    review_count = int(campaign_plan.get("candidates_reviewed", 0))
    pending_count = max(review_count - advanced_count - rejected_count, 0)
    if review_count == 0:
        decision = "pause"
        rationale = (
            f"No candidates were reviewed for {campaign_id} in run {run_id}; "
            "hold and refresh assay inputs before proceeding."
        )
    elif advanced_count > 0:
        decision = "proceed_to_next_round"
        rationale = (
            f"{advanced_count}/{review_count} candidates are advanced in run {run_id}; "
            f"{rejected_count} rejected and {pending_count} require rework."
        )
    elif rejected_count > 0 or pending_count > 0:
        decision = "rework_pool"
        rationale = (
            f"No candidates advanced for {campaign_id} in run {run_id}; "
            f"{rejected_count} rejected and the next round should focus on redesign."
        )
    else:
        decision = "rework_pool"
        rationale = (
            f"Run {run_id} did not advance any candidates for {campaign_id}; "
            "rework the pool before the next round."
        )

    top_steps = [
        item.get("step", "Underspecified next action")
        for item in next_round_plan.get("priority_focus", [])[:3]
    ]
    failure_mode_risks = [
        f"Frequent failure mode: {mode}"
        for mode, _count in campaign_plan.get("failure_mode_counts", {}).items()
    ]

    return DecisionRecord(
        decision_id=f"{campaign_id}-{run_id}-campaign-close-loop-decision",
        campaign_id=campaign_id,
        decision=decision,
        rationale=rationale,
        related_nodes=[
            f"{campaign_id}-{run_id}-campaign-recommendation-plan",
            f"{campaign_id}-{run_id}-next-round-plan",
        ],
        alternatives_considered=top_steps or [
            "Increase orthogonal assay confirmation before next synthetic run.",
            "Broaden the redesign strategy before re-pooling.",
        ],
        risks=failure_mode_risks or ["Unspecified risk mix; require additional assay replication."],
        approved_by="manual_review_loop",
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


def _validate_closed_loop_artifacts(
    *,
    recommendations_payload: dict[str, Any],
    campaign_plan: dict[str, Any],
    next_round_plan: dict[str, Any],
    campaign_decision: DecisionRecord,
) -> None:
    if not isinstance(campaign_decision, DecisionRecord):
        raise ValueError("Invalid campaign decision payload: expected DecisionRecord.")
    if not isinstance(recommendations_payload, dict):
        raise ValueError("Invalid recommendations payload: expected a mapping.")
    for key in {"run_id", "campaign_id", "count", "recommendations"}:
        if key not in recommendations_payload:
            raise ValueError(f"Invalid recommendations payload: missing key {key}.")
    run_id = recommendations_payload["run_id"]
    campaign_id = recommendations_payload["campaign_id"]
    if not run_id:
        raise ValueError("Invalid recommendations payload: run_id must be non-empty.")
    if not campaign_id:
        raise ValueError("Invalid recommendations payload: campaign_id must be non-empty.")

    if recommendations_payload.get("count", None) != len(recommendations_payload.get("recommendations", [])):
        raise ValueError("Invalid closed-loop recommendations payload: count does not match recommendations length.")
    if not isinstance(recommendations_payload.get("recommendations"), list):
        raise ValueError("Invalid recommendations payload: recommendations must be a list.")
    if not isinstance(recommendations_payload.get("count"), int):
        raise ValueError("Invalid recommendations payload: count must be an integer.")
    for entry in recommendations_payload["recommendations"]:
        if not isinstance(entry, dict):
            raise ValueError("Invalid recommendations payload: each recommendation must be a dict.")
        required_fields = {"candidate_id", "decision_id", "result_id", "status"}
        missing = required_fields - set(entry.keys())
        if missing:
            raise ValueError(
                "Invalid recommendations payload: each recommendation must include "
                f"{', '.join(sorted(missing))}."
            )
        if entry["status"] not in {CandidateStatus.ADVANCED.value, CandidateStatus.REJECTED.value}:
            raise ValueError("Invalid recommendations payload: status must be advanced or rejected.")
        if entry["candidate_id"] == "":
            raise ValueError("Invalid recommendations payload: candidate_id must be non-empty.")
        if entry["result_id"] == "":
            raise ValueError("Invalid recommendations payload: result_id must be non-empty.")
        if entry["decision_id"] == "":
            raise ValueError("Invalid recommendations payload: decision_id must be non-empty.")

    for key in {
        "run_id",
        "campaign_id",
        "candidates_reviewed",
        "status_counts",
        "failure_mode_counts",
        "prioritized_next_steps",
    }:
        if key not in campaign_plan:
            raise ValueError(f"Invalid campaign recommendation plan payload: missing key {key}.")
    if campaign_plan["run_id"] != run_id:
        raise ValueError("Invalid campaign recommendation plan payload: run_id mismatch with recommendations payload.")
    if campaign_plan["campaign_id"] != campaign_id:
        raise ValueError("Invalid campaign recommendation plan payload: campaign_id mismatch with recommendations payload.")
    if not isinstance(campaign_plan["status_counts"], dict):
        raise ValueError(
            "Invalid campaign recommendation plan payload: status_counts must be a dictionary."
        )
    if not isinstance(campaign_plan["failure_mode_counts"], dict):
        raise ValueError(
            "Invalid campaign recommendation plan payload: failure_mode_counts must be a dictionary."
        )

    for key in {"run_id", "campaign_id", "next_round_batch", "priority_focus"}:
        if key not in next_round_plan:
            raise ValueError(f"Invalid next-round planning payload: missing key {key}.")
    if next_round_plan["run_id"] != run_id:
        raise ValueError("Invalid next-round planning payload: run_id mismatch with recommendations payload.")
    if next_round_plan["campaign_id"] != campaign_id:
        raise ValueError("Invalid next-round planning payload: campaign_id mismatch with recommendations payload.")
    if not isinstance(next_round_plan["next_round_batch"], dict):
        raise ValueError("Invalid next-round planning payload: next_round_batch must be a dictionary.")
    required_next_batch_keys = {
        "advance_for_orthogonal_confirmation",
        "retest_or_rework",
        "drop_from_active_pool",
    }
    missing_next_batch_keys = required_next_batch_keys - set(
        next_round_plan["next_round_batch"].keys()
    )
    if missing_next_batch_keys:
        raise ValueError(
            "Invalid next-round planning payload: missing next_round_batch keys "
            f"{', '.join(sorted(missing_next_batch_keys))}."
        )

    if campaign_decision.decision_id == "":
        raise ValueError("Invalid campaign decision: empty decision_id.")
    if campaign_decision.campaign_id == "":
        raise ValueError("Invalid campaign decision: empty campaign_id.")
    if campaign_decision.campaign_id != campaign_id:
        raise ValueError("Invalid campaign decision: campaign_id mismatch with recommendation payload.")
    if f"{campaign_id}-{run_id}-campaign-close-loop-decision" != campaign_decision.decision_id:
        raise ValueError("Invalid campaign decision: decision_id mismatch with campaign and run identifiers.")
    if campaign_decision.decision == "":
        raise ValueError("Invalid campaign decision: empty decision.")
    if campaign_decision.decision not in {"proceed_to_next_round", "rework_pool", "pause"}:
        raise ValueError("Invalid campaign decision: unsupported decision value.")


def apply_results_to_candidates(
    candidates: Iterable[PeptideCandidate],
    results: Iterable[ExperimentalResult],
    *,
    campaign_id: str,
    run_id: str,
    output_dir: str | Path,
    dag: ResearchDAG | None = None,
    strict: bool = True,
) -> ResultReviewSummary:
    result_items = list(results)
    candidate_map = {candidate.candidate_id: candidate.model_copy(deep=True) for candidate in candidates}
    outputs: List[PeptideCandidate] = []
    decisions: List[DecisionRecord] = []
    warnings: List[str] = []
    status_transitions: List[tuple[str, CandidateStatus, CandidateStatus]] = []
    review_recommendations: List[dict[str, Any]] = []

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    records_dir = output_path / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    status_events_path = output_path / "candidate_status_events.jsonl"
    decision_events_path = output_path / "decision_events.jsonl"

    if dag is None:
        dag = ResearchDAG()
    for candidate in candidate_map.values():
        dag.add_node(candidate.candidate_id, "peptide_candidate", _format_candidate_for_dag(candidate))

    for result in result_items:
        result.failure_modes = classify_failure_modes(result, strict=strict)
        candidate = candidate_map.get(result.candidate_id)
        if candidate is None:
            message = f"No candidate found for result {result.result_id} -> {result.candidate_id}"
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        previous_status = candidate.status
        next_status = _status_from_failures(result.failure_modes)
        candidate.status = next_status
        status_transitions.append((candidate.candidate_id, previous_status, next_status))
        candidate_recommendations = _recommendations_for_failure_modes(result.failure_modes, next_status)
        result.next_action = "; ".join(candidate_recommendations)

        dag.add_node(candidate.candidate_id, "peptide_candidate", _format_candidate_for_dag(candidate))

        result_node_id = result.result_id
        dag.add_node(
            result_node_id,
            "experimental_result",
            result.model_dump(mode="json"),
        )
        dag.add_edge(candidate.candidate_id, result_node_id, "evaluated_by")

        decision_id = f"{campaign_id}-{run_id}-{candidate.candidate_id}-decision"
        decision = _build_decision_record(
            campaign_id=campaign_id,
            run_id=run_id,
            candidate=candidate,
            result=result,
            next_status=next_status,
            recommendations=candidate_recommendations,
        )
        decisions.append(decision)
        dag.add_node(
            decision_id,
            "decision_record",
            decision.model_dump(mode="json"),
        )
        dag.add_edge(candidate.candidate_id, decision_id, "decided_by")
        dag.add_edge(result_node_id, decision_id, "supported_by")

        save_json_record(candidate, records_dir / f"{candidate.candidate_id}.json")
        save_json_record(decision, records_dir / f"{decision_id}.json")
        append_jsonl(candidate, status_events_path)
        append_jsonl(decision, decision_events_path)

        review_recommendations.append(
            {
                "candidate_id": candidate.candidate_id,
                "decision_id": decision.decision_id,
                "status": candidate.status.value,
                "result_id": result.result_id,
                "failure_modes": result.failure_modes,
                "recommendations": candidate_recommendations,
            }
        )
        outputs.append(candidate)

    if not dag.validate_acyclic():
        raise ValueError("Research DAG failed acyclic validation after review integration.")

    campaign_plan = _build_campaign_recommendation_plan(
        run_id=run_id,
        campaign_id=campaign_id,
        review_recommendations=review_recommendations,
    )
    next_round_plan = _build_next_round_plan(
        run_id=run_id,
        campaign_id=campaign_id,
        campaign_plan=campaign_plan,
        review_recommendations=review_recommendations,
    )
    campaign_decision = _build_campaign_decision_record(
        campaign_id=campaign_id,
        run_id=run_id,
        campaign_plan=campaign_plan,
        next_round_plan=next_round_plan,
    )
    campaign_plan_node_id = f"{campaign_id}-{run_id}-campaign-recommendation-plan"
    dag.add_node(
        campaign_plan_node_id,
        "campaign_recommendation_plan",
        campaign_plan,
    )
    for item in review_recommendations:
        dag.add_edge(item["decision_id"], campaign_plan_node_id, "informs")

    next_round_plan_node_id = f"{campaign_id}-{run_id}-next-round-plan"
    campaign_decision_node_id = f"{campaign_id}-{run_id}-campaign-decision"
    dag.add_node(
        next_round_plan_node_id,
        "campaign_next_round_plan",
        next_round_plan,
    )
    dag.add_node(
        campaign_decision_node_id,
        "campaign_decision",
        campaign_decision.model_dump(mode="json"),
    )
    dag.add_edge(campaign_plan_node_id, next_round_plan_node_id, "drives")
    dag.add_edge(next_round_plan_node_id, campaign_decision_node_id, "supports_decision")

    _validate_closed_loop_artifacts(
        recommendations_payload={
            "run_id": run_id,
            "campaign_id": campaign_id,
            "count": len(review_recommendations),
            "recommendations": review_recommendations,
        },
        campaign_plan=campaign_plan,
        next_round_plan=next_round_plan,
        campaign_decision=campaign_decision,
    )

    (output_path / "campaign_recommendation_plan.json").write_text(
        json.dumps(campaign_plan, indent=2),
        encoding="utf-8",
    )
    (output_path / "next_round_plan.json").write_text(
        json.dumps(next_round_plan, indent=2),
        encoding="utf-8",
    )
    (output_path / "campaign_decision.json").write_text(
        json.dumps(campaign_decision.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    report_path = output_path / "result_review_report.md"
    report_lines = [
        "# Result-driven Candidate Review",
        "",
        f"Run ID: `{run_id}`",
        f"Campaign ID: `{campaign_id}`",
        f"Candidates reviewed: `{len(outputs)}`",
        "",
    ]
    for candidate in outputs:
        candidate_transition = next(
            (transition for transition in status_transitions if transition[0] == candidate.candidate_id),
            None,
        )
        if candidate_transition is None:
            note = "no transition recorded"
        else:
            note = f"{candidate_transition[1].value} -> {candidate_transition[2].value}"
        report_lines.append(f"- {candidate.candidate_id}: `{candidate.status}`")
        report_lines.append(f"  - transitions: {note}")

    if warnings:
        report_lines.append("")
        report_lines.append("## Warnings")
        report_lines.extend(f"- {warning}" for warning in warnings)

    report_lines.extend(["", "## Closed-loop recommendations"])
    if review_recommendations:
        for item in review_recommendations:
            recommendations = item["recommendations"]
            assert isinstance(recommendations, list)
            report_lines.append(f"- {item['candidate_id']} ({item['status']}):")
            for recommendation in recommendations:
                report_lines.append(f"  - {recommendation}")
    else:
        report_lines.append("- No recommendations generated.")

    report_lines.extend(
        [
            "",
            "## Campaign recommendation synthesis",
            f"- Candidates reviewed: `{campaign_plan['candidates_reviewed']}`",
            f"- Status counts: `{campaign_plan['status_counts']}`",
            "- Top prioritised next steps:",
        ]
    )
    for item in campaign_plan["prioritized_next_steps"]:
        report_lines.append(f"  - `{item['count']}`x {item['step']}")

    report_lines.extend(
        [
            "",
            "## Campaign-level decision",
            f"- decision: `{campaign_decision.decision}`",
            f"- rationale: {campaign_decision.rationale}",
        ]
    )

    recommendations_payload = {
        "run_id": run_id,
        "campaign_id": campaign_id,
        "count": len(review_recommendations),
        "recommendations": review_recommendations,
    }
    (output_path / "closed_loop_recommendations.json").write_text(
        json.dumps(recommendations_payload, indent=2),
        encoding="utf-8",
    )

    dag_payload = dag.to_dict()
    report_lines.extend(["", "## DAG snapshot", "", f"nodes: `{len(dag_payload['nodes'])}`", f"edges: `{len(dag_payload['edges'])}`"])
    report_lines.extend(["", "## Result summary", "", batch_summary_markdown(outputs)])

    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    (output_path / "research_graph_result_review.json").write_text(
        json.dumps(dag.to_dict(), indent=2),
        encoding="utf-8",
    )

    return ResultReviewSummary(
        candidates=outputs,
        results=result_items,
        decisions=decisions,
        recommendations=review_recommendations,
        campaign_recommendation_plan=campaign_plan,
        campaign_decision=campaign_decision,
        next_round_plan=next_round_plan,
        dag=dag,
        output_dir=output_path,
        report_path=report_path,
        status_transitions=status_transitions,
        warnings=warnings,
    )


def _build_decision_record(
    *,
    campaign_id: str,
    run_id: str,
    candidate: PeptideCandidate,
    result: ExperimentalResult,
    next_status: CandidateStatus,
    recommendations: list[str],
) -> DecisionRecord:
    decision = _decision_text_from_status(next_status)
    if next_status == CandidateStatus.REJECTED:
        rationale = (
            f"Candidate {candidate.candidate_id} is rejected due to inferred failures "
            f"({', '.join(result.failure_modes) or 'none'}) in result {result.result_id}."
        )
        alternatives = (
            ["Retest under alternate assay conditions", "Revisit sequence modifications"]
            + recommendations
        )
        risks = [
            f"Observed failure mode: {mode}"
            for mode in sorted(set(result.failure_modes))
        ]
    else:
        rationale = (
            f"Candidate {candidate.candidate_id} advanced because no failure modes were "
            f"inferred from result {result.result_id}."
        )
        alternatives = (
            ["Broaden orthogonal assay set", "Proceed to CRO confirmation if not already complete"]
            + recommendations
        )
        risks = ["Need reproducibility check across replicate batches."]

    return DecisionRecord(
        decision_id=f"{campaign_id}-{run_id}-{candidate.candidate_id}-decision",
        campaign_id=campaign_id,
        decision=decision,
        rationale=rationale,
        related_nodes=[candidate.candidate_id, result.result_id],
        alternatives_considered=alternatives,
        risks=risks,
    )
