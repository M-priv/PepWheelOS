from pathlib import Path
import json

from peptide_flywheel.batch_artifacts import ArtifactBatchManifest, build_batch_report_text, collect_batch_from_sources, write_batch_bundle


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_collect_batch_and_export_bundle(tmp_path: Path):
    target_path = tmp_path / "target.json"
    candidate_path = tmp_path / "candidate.json"
    invalid_candidate = tmp_path / "invalid.json"
    _write_json(
        target_path,
        {
            "target_id": "TARGET-001",
            "name": "Example",
            "organism": "human",
            "use_case": "benchmark",
            "rationale": "unit test",
        },
    )
    _write_json(
        candidate_path,
        {
            "candidate_id": "CAND-001",
            "sequence": "ACDEFGHIK",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
        },
    )
    _write_json(invalid_candidate, {"bad": "record"})

    artifacts, failures, manifest = collect_batch_from_sources(
        source_paths=[target_path, candidate_path, invalid_candidate],
        artifact_kind=None,
        recursive=False,
        strict=False,
    )
    assert len(artifacts) == 2
    assert len(failures) == 1
    assert manifest.valid_count == 2
    assert manifest.invalid_count == 1
    assert manifest.to_dict()["summary"]["valid"] == 2

    out_dir = tmp_path / "bundle"
    written = write_batch_bundle(output_dir=out_dir, manifest=manifest)
    assert written["bundle"].exists()
    assert written["jsonl"].exists()
    assert written["manifest"].exists()
    assert (out_dir / "artifacts" / "target" / "TARGET-001.json").exists()
    assert (out_dir / "artifacts" / "candidate" / "CAND-001.json").exists()


def test_batch_report_text_contains_counts_and_invalids(tmp_path):
    manifest = ArtifactBatchManifest(
        generated_at="2026-01-01T00:00:00+00:00",
        source_paths=["a"],
        strict=True,
        recursive=False,
        valid=[{"artifact_type": "target", "artifact_id": "TARGET-001"}],
        invalid=[{"artifact_type": "candidate", "source_path": "bad.json", "message": "invalid"}],
    )
    report = build_batch_report_text(manifest)
    assert "Batch Artifact Report" in report
    assert "Valid records: `1`" in report
    assert "Invalid records: `1`" in report
    assert "bad.json" in report

