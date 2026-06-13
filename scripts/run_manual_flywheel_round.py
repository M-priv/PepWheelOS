from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from peptide_flywheel.models import Hypothesis, PeptideCandidate, PeptideModality, Target
from peptide_flywheel.workflows import run_manual_flywheel_round


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a manual flywheel round from structured JSON records."
    )
    parser.add_argument("--run-id", default=None, help="Unique run identifier.")
    parser.add_argument(
        "--seed-dataset-path",
        default=None,
        help="Optional dataset CSV path to run governance checks before scoring candidates.",
    )
    parser.add_argument(
        "--split-manifest-path",
        default=None,
        help="Optional split manifest JSON for the seed dataset.",
    )
    parser.add_argument(
        "--campaign-id",
        default="CAMP-001",
        help="Campaign namespace for generated run artifact ids.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/results/manual_round",
        help="Directory where round artifacts will be written.",
    )

    parser.add_argument(
        "--target-json",
        default=None,
        help="Path to target JSON (Target schema). Optional if target args are provided.",
    )
    parser.add_argument(
        "--target-id",
        default="TARGET-001",
        help="Target identifier when --target-json is not provided.",
    )
    parser.add_argument(
        "--target-name",
        default="Example Target",
        help="Target name when --target-json is not provided.",
    )
    parser.add_argument(
        "--target-use-case",
        default="Proof of concept",
        help="Target use case when --target-json is not provided.",
    )
    parser.add_argument(
        "--target-rationale",
        default="Manual scaffold demo target.",
        help="Target rationale when --target-json is not provided.",
    )
    parser.add_argument(
        "--target-organism",
        default="unknown",
        help="Target organism when --target-json is not provided.",
    )

    parser.add_argument(
        "--hypothesis-json",
        default=None,
        help=(
            "Path to hypothesis JSON (Hypothesis schema). Optional if hypothesis args are provided."
        ),
    )
    parser.add_argument(
        "--hypothesis-id",
        default="HYP-001",
        help="Hypothesis identifier when --hypothesis-json is not provided.",
    )
    parser.add_argument(
        "--hypothesis-claim",
        default="Candidate scaffold for a placeholder claim.",
        help="Hypothesis claim when --hypothesis-json is not provided.",
    )
    parser.add_argument(
        "--hypothesis-strategy",
        default="Manual baseline candidate design.",
        help="Hypothesis design strategy when --hypothesis-json is not provided.",
    )

    parser.add_argument(
        "--candidates-json",
        default=None,
        help=(
            "Path to candidates JSON (single object or list). If omitted, a demo candidate is used."
        ),
    )
    parser.add_argument(
        "--candidate-id",
        default="CAND-001",
        help="Candidate ID for fallback demo candidate when --candidates-json is omitted.",
    )
    parser.add_argument(
        "--candidate-sequence",
        default="ACDEFGHIKLMNPQRSTVWY",
        help="Candidate sequence for fallback demo candidate when --candidates-json is omitted.",
    )
    parser.add_argument(
        "--candidate-modality",
        default="linear",
        choices=sorted([m.value for m in PeptideModality]),
        help="Candidate modality for fallback demo candidate when --candidates-json is omitted.",
    )
    parser.add_argument(
        "--skip-invalid-candidates",
        action="store_true",
        help="Skip invalid candidates instead of failing the run.",
    )
    parser.add_argument(
        "--allow-ambiguous-residues",
        action="store_true",
        help="Allow ambiguous residues B/J/O/U/X/Z while scoring.",
    )

    return parser.parse_args()


def _load_target(path: str | None, args: argparse.Namespace) -> Target:
    if path is None:
        return Target(
            target_id=args.target_id,
            name=args.target_name,
            organism=args.target_organism,
            use_case=args.target_use_case,
            rationale=args.target_rationale,
        )

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Target.model_validate(payload)


def _load_hypothesis(path: str | None, target: Target, args: argparse.Namespace) -> Hypothesis:
    if path is None:
        return Hypothesis(
            hypothesis_id=args.hypothesis_id,
            target_id=target.target_id,
            claim=args.hypothesis_claim,
            design_strategy=args.hypothesis_strategy,
        )

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Hypothesis.model_validate(payload)


def _load_candidates(
    path: str | None,
    target: Target,
    hypothesis: Hypothesis,
    args: argparse.Namespace,
) -> list[PeptideCandidate]:
    if path is None:
        return [
            PeptideCandidate(
                candidate_id=args.candidate_id,
                sequence=args.candidate_sequence,
                target_id=target.target_id,
                hypothesis_id=hypothesis.hypothesis_id,
                modality=PeptideModality(args.candidate_modality),
                design_rationale="Fallback demo candidate generated by CLI.",
            )
        ]

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("--candidates-json must contain a JSON object or list of objects.")

    return [PeptideCandidate.model_validate(item) for item in payload]


def main() -> None:
    args = _parse_args()
    run_id = args.run_id or f"run-{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    target = _load_target(args.target_json, args)
    hypothesis = _load_hypothesis(args.hypothesis_json, target, args)
    candidates = _load_candidates(args.candidates_json, target, hypothesis, args)

    result = run_manual_flywheel_round(
        target=target,
        hypothesis=hypothesis,
        candidates=candidates,
        run_id=run_id,
        campaign_id=args.campaign_id,
        seed_dataset_path=args.seed_dataset_path,
        split_manifest_path=args.split_manifest_path,
        output_dir=args.output_dir,
        strict=not args.skip_invalid_candidates,
        allow_ambiguous_residues=args.allow_ambiguous_residues,
    )

    print(f"Manual flywheel round complete. Run ID: {run_id}")
    print(f"Artifacts written to: {result.output_dir}")
    print(f"Report: {result.report_path}")
    print(f"Candidates scored: {len(result.candidates)}")
    if result.validation_errors:
        print(f"Validation errors: {len(result.validation_errors)}")
        for err in result.validation_errors:
            print(f"  - ERROR: {err}")
    if result.validation_warnings:
        print(f"Validation warnings: {len(result.validation_warnings)}")
        for warn in result.validation_warnings:
            print(f"  - WARN: {warn}")
    if result.data_governance_events:
        print(f"Data governance events: {len(result.data_governance_events)}")
        for event in result.data_governance_events:
            print(f"  - {event}")
    if result.data_governance_report_path:
        print(f"Data governance report: {result.data_governance_report_path}")
    print(result.summary_markdown)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"Run failed: {exc}")
        sys.exit(1)
