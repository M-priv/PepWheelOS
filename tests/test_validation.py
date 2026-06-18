from pathlib import Path

import json
import pytest

from peptide_flywheel.validation import build_validation_report, validate_json_artifacts


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_validate_json_artifacts_accepts_valid_inputs(tmp_path):
    target_path = tmp_path / "target.json"
    candidate_path = tmp_path / "candidate.json"
    _write_json(
        target_path,
        {
            "target_id": "TARGET-001",
            "name": "Example target",
            "organism": "human",
            "use_case": "benchmark",
            "rationale": "unit test",
        },
    )
    _write_json(
        candidate_path,
        {
            "candidate_id": "CAND-001",
            "sequence": "ACDEFG",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
        },
    )

    artifacts, failures = validate_json_artifacts(
        [str(target_path), str(candidate_path)],
        strict=False,
    )

    assert len(artifacts) == 2
    assert not failures
    assert {item.artifact_kind for item in artifacts} == {"target", "candidate"}

    report = build_validation_report(artifacts=artifacts, failures=failures, source_paths=[target_path, candidate_path])
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 0


def test_validate_json_artifacts_lenient_collects_invalid_payload(tmp_path):
    bad_candidate = tmp_path / "bad_candidate.json"
    _write_json(
        bad_candidate,
        {
            "candidate_id": "BAD-001",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
        },
    )
    artifacts, failures = validate_json_artifacts(
        [str(bad_candidate)],
        artifact_kind="candidate",
        strict=False,
    )
    assert not artifacts
    assert len(failures) == 1
    assert "sequence" in failures[0].message


def test_validate_json_artifacts_strict_fails_on_validation_error(tmp_path):
    bad_candidate = tmp_path / "bad_candidate.json"
    _write_json(
        bad_candidate,
        {
            "candidate_id": "BAD-001",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
        },
    )
    with pytest.raises(ValueError, match="JSON artifact validation failed"):
        validate_json_artifacts(
            [str(bad_candidate)],
            artifact_kind="candidate",
            strict=True,
        )

