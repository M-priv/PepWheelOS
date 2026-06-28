from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pydantic import ValidationError

from peptide_flywheel.active_learning import run_active_learning_simulation
from peptide_flywheel.dag import ResearchDAG
from peptide_flywheel.models import PeptideCandidate
from peptide_flywheel.storage import load_json_record


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the phase-2 active-learning simulator over candidate records."
    )
    parser.add_argument(
        "--candidate-record",
        action="append",
        default=[],
        help="Candidate JSON record to include (repeatable).",
    )
    parser.add_argument(
        "--candidate-records-dir",
        default="data/results/manual_round/records",
        help="Directory containing candidate JSON records.",
    )
    parser.add_argument("--campaign-id", default="CAMP-001", help="Campaign namespace.")
    parser.add_argument("--run-id", default=None, help="Run identifier.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of candidates to select for the next simulated batch.",
    )
    parser.add_argument(
        "--exploitation-weight",
        type=float,
        default=0.55,
        help="Weight for manufacturability score.",
    )
    parser.add_argument(
        "--exploration-weight",
        type=float,
        default=0.30,
        help="Weight for sequence diversity / novelty.",
    )
    parser.add_argument(
        "--uncertainty-weight",
        type=float,
        default=0.15,
        help="Weight for uncertainty sampling near the decision boundary.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/phase2/active_learning",
        help="Directory where simulator artifacts are written.",
    )
    parser.add_argument(
        "--base-dag-json",
        default=None,
        help="Optional existing research_graph.json to merge active-learning nodes into.",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Skip malformed explicit candidate files instead of failing.",
    )
    return parser.parse_args()


def _load_candidate_file(path: Path, *, strict: bool) -> list[PeptideCandidate]:
    try:
        return [load_json_record(PeptideCandidate, path)]
    except (ValidationError, ValueError, TypeError, json.JSONDecodeError):
        if strict:
            raise ValueError(f"Not a candidate record: {path}")
        return []


def _load_candidates(
    *,
    explicit_paths: list[str],
    records_dir: str,
    strict: bool,
) -> list[PeptideCandidate]:
    candidates: list[PeptideCandidate] = []
    for raw_path in explicit_paths:
        candidates.extend(_load_candidate_file(Path(raw_path), strict=strict))

    directory = Path(records_dir)
    if directory.exists():
        for item in sorted(directory.glob("*.json")):
            candidates.extend(_load_candidate_file(item, strict=False))

    deduped: dict[str, PeptideCandidate] = {}
    for candidate in candidates:
        deduped[candidate.candidate_id] = candidate
    return sorted(deduped.values(), key=lambda item: item.candidate_id)


def _load_base_dag(path: str | None) -> ResearchDAG | None:
    if path is None:
        return None
    dag_path = Path(path)
    if not dag_path.exists():
        raise ValueError(f"Base DAG file not found: {dag_path}")
    return ResearchDAG.from_dict(json.loads(dag_path.read_text(encoding="utf-8")))


def main() -> None:
    args = _parse_args()
    run_id = args.run_id or f"run-{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    strict = not args.lenient
    candidates = _load_candidates(
        explicit_paths=args.candidate_record,
        records_dir=args.candidate_records_dir,
        strict=strict,
    )
    if not candidates:
        raise ValueError("No candidate records loaded.")

    base_dag = _load_base_dag(args.base_dag_json)
    result = run_active_learning_simulation(
        candidates=candidates,
        campaign_id=args.campaign_id,
        run_id=run_id,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        exploitation_weight=args.exploitation_weight,
        exploration_weight=args.exploration_weight,
        uncertainty_weight=args.uncertainty_weight,
        dag=base_dag,
    )

    if base_dag is not None:
        base_path = Path(args.base_dag_json)
        base_path.write_text(json.dumps(result.dag.to_dict(), indent=2), encoding="utf-8")
        print(f"Merged campaign DAG updated: {base_path}")

    print(f"Active-learning simulation complete for run {run_id}.")
    print(f"Candidates ranked: {len(result.rankings)}")
    print(f"Selected: {', '.join(result.selected_candidate_ids)}")
    print(f"Output dir: {result.output_dir}")
    print(f"Report: {result.report_path}")
    print("Artifacts:")
    print(f"- {result.plan_path}")
    print(f"- {result.rankings_path}")
    print(f"- {result.prompt_path}")
    print(f"- {result.output_dir / 'research_graph_active_learning.json'}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Active-learning simulation failed: {exc}")
        sys.exit(1)
