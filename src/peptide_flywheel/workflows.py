from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Iterable, List

from .dag import ResearchDAG
from .models import (
    CandidateStatus,
    Hypothesis,
    ManufacturabilityAssessment,
    PeptideCandidate,
    PredictionRun,
    Target,
)
from .reporting import batch_summary_markdown, candidate_card_markdown
from .scoring import heuristic_manufacturability_score
from .storage import append_jsonl, save_json_record
from .data_governance import run_data_governance_preflight


AMINO_STANDARD = set("ACDEFGHIKLMNPQRSTVWY")
AMINO_AMBIGUOUS = set("BJOUXZ")
VALID_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass
class ManualFlywheelRoundResult:
    target: Target
    hypothesis: Hypothesis
    candidates: List[PeptideCandidate]
    prediction_runs: List[PredictionRun]
    assessments: List[ManufacturabilityAssessment]
    dag: ResearchDAG
    output_dir: Path
    report_path: Path
    summary_markdown: str
    validation_errors: List[str]
    validation_warnings: List[str]
    data_governance_events: List[dict] = field(default_factory=list)
    data_governance_report_path: Path | None = None


def _validate_identifier(value: str, label: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{label} is required and cannot be empty.")

    if not VALID_ID_PATTERN.match(value):
        raise ValueError(
            f"{label} '{value}' has invalid characters. "
            "Allowed characters are letters, digits, '.', '-', and '_'."
        )
    return value


def _validate_candidate_sequence(sequence: str, allow_ambiguous: bool = False) -> tuple[str, List[str]]:
    normalized = (sequence or "").strip().upper()
    if not normalized:
        raise ValueError("sequence is required and cannot be empty.")

    unknown_residues = sorted(set(normalized) - (AMINO_STANDARD | AMINO_AMBIGUOUS))
    if unknown_residues:
        raise ValueError(f"unsupported residues: {''.join(unknown_residues)}")

    warnings: List[str] = []
    ambiguous_residues = sorted(set(normalized) & AMINO_AMBIGUOUS)
    if ambiguous_residues and not allow_ambiguous:
        raise ValueError(f"ambiguous residues: {''.join(ambiguous_residues)}")

    if ambiguous_residues:
        warnings.append(f"ambiguous residues observed: {''.join(ambiguous_residues)}")

    return normalized, warnings


def run_manual_flywheel_round(
    *,
    target: Target,
    hypothesis: Hypothesis,
    candidates: Iterable[PeptideCandidate],
    run_id: str,
    seed_dataset_path: str | Path | None = None,
    split_manifest_path: str | Path | None = None,
    output_dir: str | Path,
    campaign_id: str | None = None,
    strict: bool = True,
    allow_ambiguous_residues: bool = False,
) -> ManualFlywheelRoundResult:
    candidate_list = list(candidates)
    if not candidate_list:
        raise ValueError("At least one candidate is required for a manual round.")

    target = target.model_copy(deep=True)
    hypothesis = hypothesis.model_copy(deep=True)

    target_id = _validate_identifier(target.target_id, "target_id")
    target.target_id = target_id
    hypothesis_id = _validate_identifier(hypothesis.hypothesis_id, "hypothesis_id")
    if hypothesis.target_id != target_id:
        if strict:
            raise ValueError(
                f"Hypothesis {hypothesis_id} target mismatch: "
                f"{hypothesis.target_id} != {target_id}"
            )
        target_id = hypothesis.target_id
    hypothesis.hypothesis_id = hypothesis_id
    hypothesis.target_id = target_id

    if campaign_id is None:
        campaign_id = "CAMP-001"
    campaign_id = _validate_identifier(campaign_id, "campaign_id")
    run_id = _validate_identifier(run_id, "run_id")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    records_dir = output_path / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    cards_dir = output_path / "candidate_cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    candidate_events_path = output_path / "candidate_events.jsonl"
    prediction_events_path = output_path / "prediction_events.jsonl"
    assessment_events_path = output_path / "assessment_events.jsonl"

    dag = ResearchDAG()
    dag.add_node(target.target_id, "target", target.model_dump(mode="json"))
    dag.add_node(hypothesis.hypothesis_id, "hypothesis", hypothesis.model_dump(mode="json"))
    dag.add_edge(target.target_id, hypothesis.hypothesis_id, "supports")

    scored_candidates: List[PeptideCandidate] = []
    prediction_runs: List[PredictionRun] = []
    assessments: List[ManufacturabilityAssessment] = []
    candidate_cards: List[str] = []
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    data_governance_events: List[dict] = []
    data_governance_report_path: Path | None = None
    if seed_dataset_path is not None:
        preflight = run_data_governance_preflight(
            dataset_csv_path=seed_dataset_path,
            split_manifest_path=split_manifest_path,
            strict=False,
            allow_ambiguous_residues=allow_ambiguous_residues,
        )
        data_governance_events = [event.to_dict() for event in preflight.events]
        for event in preflight.events:
            if event.severity == "error":
                validation_errors.append(event.as_text)
            elif event.severity == "warning":
                validation_warnings.append(event.as_text)

        data_governance_report_path = output_path / "data_governance_preflight.json"
        data_governance_report_path.write_text(
            json.dumps(preflight.as_dict(), indent=2),
            encoding="utf-8",
        )

        if strict and preflight.error_count > 0:
            raise ValueError(
                f"Data governance preflight failed for {seed_dataset_path}: "
                f"{preflight.error_count} error(s)."
            )

    seen_candidate_ids = set[str]()

    for raw_candidate in candidate_list:
        if not raw_candidate.candidate_id:
            message = "candidate_id is required."
            if strict:
                raise ValueError(message)
            validation_errors.append(f"Candidate [missing id]: {message}")
            continue

        try:
            candidate = raw_candidate.model_copy(deep=True)
            candidate.candidate_id = _validate_identifier(candidate.candidate_id, "candidate_id")
        except ValueError as exc:
            if strict:
                raise
            validation_errors.append(f"Candidate '{raw_candidate.candidate_id}': {exc}")
            continue

        if candidate.candidate_id in seen_candidate_ids:
            message = f"Duplicate candidate_id found: {candidate.candidate_id}"
            if strict:
                raise ValueError(message)
            validation_errors.append(message)
            continue
        seen_candidate_ids.add(candidate.candidate_id)

        try:
            candidate.sequence, warnings = _validate_candidate_sequence(
                candidate.sequence,
                allow_ambiguous=allow_ambiguous_residues,
            )
            for warning in warnings:
                validation_warnings.append(f"{candidate.candidate_id}: {warning}")
        except ValueError as exc:
            if strict:
                raise
            validation_errors.append(f"Candidate {candidate.candidate_id}: sequence invalid: {exc}")
            continue

        try:
            candidate.target_id = _validate_identifier(candidate.target_id, "candidate target_id")
        except ValueError as exc:
            if strict:
                raise
            validation_errors.append(f"Candidate {candidate.candidate_id}: {exc}")
            continue

        try:
            candidate.hypothesis_id = _validate_identifier(candidate.hypothesis_id, "candidate hypothesis_id")
        except ValueError as exc:
            if strict:
                raise
            validation_errors.append(f"Candidate {candidate.candidate_id}: {exc}")
            continue

        if candidate.target_id != target_id:
            message = (
                f"{candidate.candidate_id} target mismatch: "
                f"{candidate.target_id} != {target_id}"
            )
            if strict:
                raise ValueError(message)
            validation_errors.append(message)
            continue

        if candidate.hypothesis_id != hypothesis_id:
            message = (
                f"{candidate.candidate_id} hypothesis mismatch: "
                f"{candidate.hypothesis_id} != {hypothesis_id}"
            )
            if strict:
                raise ValueError(message)
            validation_errors.append(message)
            continue

        score = heuristic_manufacturability_score(candidate.sequence, candidate.modality.value)

        candidate.manufacturability_score = score.overall_score
        candidate.risk_flags = score.risk_flags
        candidate.predicted_properties = score.dimension_scores
        if candidate.status == CandidateStatus.DRAFT:
            candidate.status = CandidateStatus.SCORED

        prediction_run = PredictionRun(
            prediction_id=f"{campaign_id}-{run_id}-{candidate.candidate_id}-pred",
            candidate_id=candidate.candidate_id,
            tool_name="heuristic_manufacturability_score",
            tool_version="0.1.0",
            input_refs=[run_id, candidate.candidate_id],
            outputs={
                "overall_score": score.overall_score,
                "risk_flags": score.risk_flags,
                "dimension_scores": score.dimension_scores,
            },
            interpretation=score.recommendation,
            uncertainty="heuristic",
        )

        assessment = ManufacturabilityAssessment(
            assessment_id=f"{campaign_id}-{run_id}-{candidate.candidate_id}-manu",
            candidate_id=candidate.candidate_id,
            dimension_scores=score.dimension_scores,
            overall_score=score.overall_score,
            risk_flags=score.risk_flags,
            mitigation_notes=[],
            recommendation=score.recommendation,
        )

        dag.add_node(candidate.candidate_id, "peptide_candidate", candidate.model_dump(mode="json"))
        dag.add_node(
            prediction_run.prediction_id,
            "prediction_run",
            prediction_run.model_dump(mode="json"),
        )
        dag.add_node(
            assessment.assessment_id,
            "manufacturability_assessment",
            assessment.model_dump(mode="json"),
        )

        dag.add_edge(hypothesis.hypothesis_id, candidate.candidate_id, "generated")
        dag.add_edge(candidate.candidate_id, prediction_run.prediction_id, "evaluated_by")
        dag.add_edge(prediction_run.prediction_id, assessment.assessment_id, "informed")
        dag.add_edge(candidate.candidate_id, assessment.assessment_id, "assessed_by")

        scored_candidates.append(candidate)
        prediction_runs.append(prediction_run)
        assessments.append(assessment)

        save_json_record(candidate, records_dir / f"{candidate.candidate_id}.json")
        save_json_record(prediction_run, records_dir / f"{prediction_run.prediction_id}.json")
        save_json_record(assessment, records_dir / f"{assessment.assessment_id}.json")

        append_jsonl(candidate, candidate_events_path)
        append_jsonl(prediction_run, prediction_events_path)
        append_jsonl(assessment, assessment_events_path)

        candidate_cards.append(candidate_card_markdown(candidate))

    if strict and not scored_candidates:
        raise ValueError("No valid candidates were processed in strict mode.")

    if not dag.validate_acyclic():
        raise ValueError("Research DAG failed acyclic validation.")

    dag_json = dag.to_dict()
    (output_path / "research_graph.json").write_text(
        json.dumps(dag_json, indent=2),
        encoding="utf-8",
    )

    summary = batch_summary_markdown(scored_candidates)
    report_lines = [
        "# Manual Flywheel Round",
        "",
        f"Run ID: `{run_id}`",
        f"Campaign ID: `{campaign_id}`",
        f"Target: `{target.target_id}`",
        f"Hypothesis: `{hypothesis.hypothesis_id}`",
        f"Total candidates: `{len(scored_candidates)}`",
        f"Timestamp (UTC): `{datetime.now(tz=timezone.utc).isoformat()}`",
        "",
        f"- DAG nodes: `{len(dag_json['nodes'])}`",
        f"- DAG edges: `{len(dag_json['edges'])}`",
        "",
    ]

    if validation_errors:
        report_lines.append(f"- Validation errors: `{len(validation_errors)}`")
        report_lines.extend(f"  - ERROR: {msg}" for msg in validation_errors)
    if validation_warnings:
        report_lines.append(f"- Validation warnings: `{len(validation_warnings)}`")
        report_lines.extend(f"  - WARN: {msg}" for msg in validation_warnings)
    if data_governance_events:
        report_lines.append(f"- Data-governance events: `{len(data_governance_events)}`")
        report_lines.extend(f"  - GOVERNANCE: {event.get('code')} {event.get('severity')}: {event.get('message')}" for event in data_governance_events)

    if not validation_errors and not validation_warnings:
        report_lines.append("- Validation: `passed`")
    if data_governance_report_path is not None:
        report_lines.append(f"- Data governance report: `{data_governance_report_path}`")

    report_lines.extend(["", "## Batch summary", summary, "", "## Candidate cards"])
    for card in candidate_cards:
        report_lines.append(f"\n---\n\n{card}")

    report_path = output_path / "round_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return ManualFlywheelRoundResult(
        target=target,
        hypothesis=hypothesis,
        candidates=scored_candidates,
        prediction_runs=prediction_runs,
        assessments=assessments,
        dag=dag,
        output_dir=output_path,
        report_path=report_path,
        summary_markdown=summary,
        validation_errors=validation_errors,
        validation_warnings=validation_warnings,
        data_governance_events=data_governance_events,
        data_governance_report_path=data_governance_report_path,
    )
