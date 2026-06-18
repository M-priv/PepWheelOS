from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from .validation import (
    ArtifactValidationFailure,
    ValidatedArtifact,
    artifact_id_from_model,
    validate_json_artifacts,
)


@dataclass
class ArtifactBatchManifest:
    generated_at: str
    source_paths: list[str]
    strict: bool
    recursive: bool
    valid: list[dict[str, Any]] = field(default_factory=list)
    invalid: list[dict[str, Any]] = field(default_factory=list)

    @property
    def valid_count(self) -> int:
        return len(self.valid)

    @property
    def invalid_count(self) -> int:
        return len(self.invalid)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "source_paths": self.source_paths,
            "strict": self.strict,
            "recursive": self.recursive,
            "summary": {
                "valid": self.valid_count,
                "invalid": self.invalid_count,
            },
            "valid": self.valid,
            "invalid": self.invalid,
        }


def _build_valid_payloads(
    artifacts: list[ValidatedArtifact],
) -> list[dict[str, Any]]:
    return [
        {
            "artifact_type": artifact.artifact_kind,
            "artifact_id": artifact_id_from_model(artifact.model, artifact.artifact_kind),
            "source_path": str(artifact.source),
            "payload_index": artifact.payload_index,
            "payload": artifact.payload,
        }
        for artifact in artifacts
    ]


def _build_invalid_payloads(
    failures: list[ArtifactValidationFailure],
) -> list[dict[str, Any]]:
    return [
        {
            "artifact_type": failure.artifact_kind,
            "source_path": str(failure.source),
            "payload_index": failure.payload_index,
            "message": failure.message,
        }
        for failure in failures
    ]


def _summarize_by_type(items: list[dict[str, Any]]) -> dict[str, int]:
    tally: dict[str, int] = {}
    for item in items:
        key = str(item.get("artifact_type", "unknown"))
        tally[key] = tally.get(key, 0) + 1
    return tally


def build_manifest(
    *,
    source_paths: list[str],
    artifacts: list[ValidatedArtifact],
    failures: list[ArtifactValidationFailure],
    strict: bool,
    recursive: bool,
) -> ArtifactBatchManifest:
    return ArtifactBatchManifest(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        source_paths=source_paths,
        strict=strict,
        recursive=recursive,
        valid=_build_valid_payloads(artifacts),
        invalid=_build_invalid_payloads(failures),
    )


def write_batch_bundle(
    *,
    output_dir: Path,
    manifest: ArtifactBatchManifest,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "batch_manifest.json"
    jsonl_path = output_dir / "batch_records.jsonl"
    bundle_path = output_dir / "batch_records.json"
    report_path = output_dir / "batch_report.md"
    artifact_dir = output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2),
        encoding="utf-8",
    )

    valid_records = manifest.valid
    bundle_path.write_text(
        json.dumps(valid_records, indent=2),
        encoding="utf-8",
    )
    with jsonl_path.open("w", encoding="utf-8") as fp:
        for item in valid_records:
            fp.write(json.dumps(item, sort_keys=True) + "\n")

    for item in valid_records:
        kind = item["artifact_type"]
        artifact_id = str(item.get("artifact_id") or "unknown")
        destination_dir = artifact_dir / kind
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{artifact_id}.json"
        if destination.exists():
            destination = destination_dir / f"{artifact_id}-{item.get('payload_index', '0')}.json"
        destination.write_text(
            json.dumps(item["payload"], indent=2),
            encoding="utf-8",
        )

    report_path.write_text(
        build_batch_report_text(manifest),
        encoding="utf-8",
    )

    return {
        "manifest": manifest_path,
        "bundle": bundle_path,
        "jsonl": jsonl_path,
        "report": report_path,
        "artifact_dir": artifact_dir,
    }


def build_batch_report_text(manifest: ArtifactBatchManifest) -> str:
    lines = [
        "# Batch Artifact Report",
        "",
        f"Generated: {manifest.generated_at}",
        f"Source paths: {', '.join(manifest.source_paths) or 'none'}",
        "",
        f"- Valid records: `{manifest.valid_count}`",
        f"- Invalid records: `{manifest.invalid_count}`",
        "",
        "## Valid artifact summary",
    ]

    for kind, count in sorted(_summarize_by_type(manifest.valid).items()):
        lines.append(f"- {kind}: `{count}`")

    if manifest.invalid:
        lines.append("")
        lines.append("## Invalid artifacts")
        for item in manifest.invalid:
            lines.append(
                f"- {item.get('artifact_type') or 'unknown'} from {item.get('source_path')}: "
                f"{item.get('message')}"
            )
    else:
        lines.append("")
        lines.append("## Invalid artifacts")
        lines.append("- None")

    return "\n".join(lines)


def collect_batch_from_sources(
    *,
    source_paths: list[Path],
    artifact_kind: str | None = None,
    recursive: bool = False,
    strict: bool = True,
) -> tuple[list[ValidatedArtifact], list[ArtifactValidationFailure], ArtifactBatchManifest]:
    raw_artifacts, failures = validate_json_artifacts(
        source_paths,
        artifact_kind=artifact_kind,
        recursive=recursive,
        strict=False,
    )
    manifest = build_manifest(
        source_paths=[str(path) for path in source_paths],
        artifacts=raw_artifacts,
        failures=failures,
        strict=strict,
        recursive=recursive,
    )
    if failures and strict:
        raise ValueError(build_batch_report_text(manifest))
    return raw_artifacts, failures, manifest

