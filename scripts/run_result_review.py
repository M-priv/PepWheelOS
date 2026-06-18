from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pydantic import ValidationError

from peptide_flywheel.dag import ResearchDAG
from peptide_flywheel.models import CandidateStatus, ExperimentalResult, PeptideCandidate
from peptide_flywheel.result_ingestion import parse_experimental_result_file
from peptide_flywheel.result_review import apply_results_to_candidates
from peptide_flywheel.storage import load_json_record


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Attach simulated/external experimental results to candidate records."
    )
    parser.add_argument(
        "--candidate-record",
        action="append",
        default=[],
        help="Candidate JSON records to include in review (repeatable).",
    )
    parser.add_argument(
        "--candidate-records-dir",
        default="data/results/manual_round/records",
        help="Directory with candidate JSON records.",
    )
    parser.add_argument(
        "--result",
        action="append",
        default=[],
        required=True,
        help="Experimental result file paths (repeatable).",
    )
    parser.add_argument(
        "--campaign-id",
        default="CAMP-001",
        help="Campaign namespace for generated decision IDs.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run identifier for decision IDs.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/results/manual_round",
        help="Directory where candidate updates are written.",
    )
    parser.add_argument(
        "--base-dag-json",
        default=None,
        help=(
            "Optional campaign DAG JSON file to merge review outputs into "
            "(e.g. research_graph.json)."
        ),
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Skip malformed result files or unmatched candidates.",
    )
    return parser.parse_args()


def _load_candidate_records(paths: list[str], records_dir: str, strict: bool) -> list[PeptideCandidate]:
    candidates: list[PeptideCandidate] = []
    for raw_path in paths:
        path = Path(raw_path)
        candidates.extend(_load_candidate_records_from_file(path, strict=strict, require_candidate=True))

    records_directory = Path(records_dir)
    if records_directory.exists():
        for item in sorted(records_directory.glob("*.json")):
            candidates.extend(_load_candidate_records_from_file(item, strict=False, require_candidate=False))

    deduped: dict[str, PeptideCandidate] = {}
    for candidate in candidates:
        deduped[candidate.candidate_id] = candidate
    return list(deduped.values())


def _load_candidate_records_from_file(
    path: Path,
    *,
    strict: bool,
    require_candidate: bool,
) -> list[PeptideCandidate]:
    payload = path.read_text(encoding="utf-8")
    if not payload.strip():
        if strict:
            raise ValueError(f"Empty candidate file: {path}")
        return []
    try:
        candidate = load_json_record(PeptideCandidate, path)
    except (ValidationError, ValueError, TypeError):
        if strict and require_candidate:
            raise ValueError(f"Not a candidate record: {path}")
        return []
    if candidate.status not in {CandidateStatus.DRAFT, CandidateStatus.SCORED, CandidateStatus.TESTED, CandidateStatus.SELECTED}:
        candidate.status = CandidateStatus.SCORED
    return [candidate]


def _load_base_dag(path: str | None) -> ResearchDAG | None:
    if path is None:
        return None
    dag_path = Path(path)
    if not dag_path.exists():
        raise ValueError(f"Base DAG file not found: {dag_path}")
    payload = json.loads(dag_path.read_text(encoding="utf-8"))
    return ResearchDAG.from_dict(payload)


def _load_results(paths: list[str], strict: bool) -> list[ExperimentalResult]:
    parsed: list[ExperimentalResult] = []
    for raw in paths:
        result_path = Path(raw)
        try:
            parsed.append(parse_experimental_result_file(result_path, strict=strict))
        except ValueError as exc:
            if strict:
                raise ValueError(f"Failed to parse {result_path}: {exc}")
            print(f"WARN: skipping {result_path}: {exc}")
    return parsed


def main() -> None:
    args = _parse_args()
    strict = not args.lenient
    run_id = args.run_id or f"run-{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    candidates = _load_candidate_records(
        paths=args.candidate_record,
        records_dir=args.candidate_records_dir,
        strict=strict,
    )
    if not candidates:
        raise ValueError("No candidate records loaded.")

    results = _load_results(paths=args.result, strict=strict)
    if not results:
        raise ValueError("No usable results loaded.")
    base_dag = _load_base_dag(args.base_dag_json)

    result = apply_results_to_candidates(
        candidates=candidates,
        results=results,
        campaign_id=args.campaign_id,
        run_id=run_id,
        output_dir=args.output_dir,
        dag=base_dag,
        strict=strict,
    )

    if base_dag is not None:
        main_graph_path = Path(args.base_dag_json)
        main_graph_path.write_text(
            json.dumps(result.dag.to_dict(), indent=2),
            encoding="utf-8",
        )
        print(f"Merged campaign DAG updated: {main_graph_path}")

    print(f"Result review complete for run {run_id}.")
    print(f"Output dir: {result.output_dir}")
    print(f"Report: {result.report_path}")
    print("Artifacts:")
    print(f"- {result.output_dir / 'closed_loop_recommendations.json'}")
    print(f"- {result.output_dir / 'campaign_recommendation_plan.json'}")
    print(f"- {result.output_dir / 'next_round_plan.json'}")
    print(f"- {result.output_dir / 'campaign_decision.json'}")
    print(f"- {result.output_dir / 'research_graph_result_review.json'}")
    for candidate in result.candidates:
        print(f"- {candidate.candidate_id}: {candidate.status}")
    for warning in result.warnings:
        print(f"WARN: {warning}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Result review failed: {exc}")
        sys.exit(1)
