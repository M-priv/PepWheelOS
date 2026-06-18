from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pydantic import ValidationError

from peptide_flywheel.models import Hypothesis, PeptideCandidate, Target
from peptide_flywheel.prompt_pipeline import build_prompt_batch, prompt_manifest
from peptide_flywheel.validation import (
    validate_json_artifacts,
    artifact_id_from_model,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build structured prompt packets for the phase-2 semi-automated pipeline."
    )
    parser.add_argument("--target-json", required=True, help="Path to target JSON artifact.")
    parser.add_argument(
        "--hypothesis-json",
        required=True,
        help="Path to hypothesis JSON artifact.",
    )
    parser.add_argument(
        "--candidates-json",
        default=None,
        help=(
            "Path to candidate JSON artifacts (single object, list, or JSON array/list file). "
            "Cannot be used with --candidate-dir."
        ),
    )
    parser.add_argument(
        "--candidate-dir",
        default=None,
        help="Directory containing candidate JSON files; candidate object files must each validate.",
    )
    parser.add_argument(
        "--campaign-id",
        default="CAMP-001",
        help="Campaign context id.",
    )
    parser.add_argument(
        "--run-id",
        default="RUN-0001",
        help="Prompt batch run identifier.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/phase2/prompt_batch",
        help="Output directory for prompt JSON packets and manifest.",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Keep working with partially valid candidate artifacts.",
    )
    return parser.parse_args()


def _load_target(path: Path) -> Target:
    artifacts, failures = validate_json_artifacts([path], artifact_kind="target", strict=False)
    if not artifacts:
        raise ValueError(f"No valid target loaded from {path}: {failures[0].message if failures else 'unknown'}")
    if len(artifacts) > 1:
        raise ValueError(f"Expected one target but found {len(artifacts)} in {path}")
    return artifacts[0].model


def _load_hypothesis(path: Path) -> Hypothesis:
    artifacts, failures = validate_json_artifacts([path], artifact_kind="hypothesis", strict=False)
    if not artifacts:
        raise ValueError(f"No valid hypothesis loaded from {path}: {failures[0].message if failures else 'unknown'}")
    if len(artifacts) > 1:
        raise ValueError(f"Expected one hypothesis but found {len(artifacts)} in {path}")
    return artifacts[0].model


def _load_candidates(
    *,
    candidates_json: str | None,
    candidate_dir: str | None,
    lenient: bool,
) -> list[PeptideCandidate]:
    if not candidates_json and not candidate_dir:
        raise ValueError("Either --candidates-json or --candidate-dir is required.")
    if candidates_json and candidate_dir:
        raise ValueError("Use one of --candidates-json or --candidate-dir, not both.")

    source: list[str | Path] = [candidates_json or candidate_dir]  # type: ignore[list-item]

    artifacts, failures = validate_json_artifacts(
        source,
        artifact_kind="candidate",
        recursive=bool(candidate_dir),
        strict=False,
    )
    if failures and not lenient:
        first_error = failures[0].message
        raise ValueError(f"Candidate artifact validation failed: {first_error}")

    if not artifacts:
        raise ValueError("No valid candidates loaded.")

    candidates = [artifact.model for artifact in artifacts]
    return sorted(candidates, key=lambda item: item.candidate_id)


def _save_outputs(
    output_dir: Path,
    packets: list,
    manifest: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir.joinpath("prompt_batch_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    manifest_index_path = output_dir / "prompt_batch.jsonl"
    with manifest_index_path.open("w", encoding="utf-8") as fp:
        for packet in packets:
            fp.write(json.dumps(packet.model_dump(), sort_keys=True) + "\n")

    per_agent_dir = output_dir / "packets"
    per_agent_dir.mkdir(parents=True, exist_ok=True)
    for packet in packets:
        artifact_name = f"{packet.packet_id}.json"
        payload_path = per_agent_dir / artifact_name
        payload_path.write_text(json.dumps(packet.model_dump(), indent=2), encoding="utf-8")


def main() -> None:
    args = _parse_args()
    strict_or_lenient = not args.lenient

    target = _load_target(Path(args.target_json))
    hypothesis = _load_hypothesis(Path(args.hypothesis_json))
    candidates = _load_candidates(
        candidates_json=args.candidates_json,
        candidate_dir=args.candidate_dir,
        lenient=args.lenient,
    )

    packets = build_prompt_batch(
        target=target,
        hypothesis=hypothesis,
        candidates=candidates,
        campaign_id=args.campaign_id,
        run_id=args.run_id,
    )
    if not packets:
        raise ValueError("No prompt packets were produced.")

    manifest = prompt_manifest(packets)
    manifest["source"] = {
        "target": artifact_id_from_model(target, "target"),
        "hypothesis": artifact_id_from_model(hypothesis, "hypothesis"),
        "candidates": [artifact_id_from_model(candidate, "candidate") for candidate in candidates],
        "campaign_id": args.campaign_id,
        "run_id": args.run_id,
        "lenient": args.lenient,
        "strict": strict_or_lenient,
    }

    _save_outputs(Path(args.output_dir), packets, manifest)
    print(f"Generated {len(packets)} prompt packets in {args.output_dir}")
    print(f"Manifest: {Path(args.output_dir) / 'prompt_batch_manifest.json'}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ValidationError) as exc:
        print(f"Prompt batch generation failed: {exc}")
        raise SystemExit(1)

