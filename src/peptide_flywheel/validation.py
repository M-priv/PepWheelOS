from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence
import json

from pydantic import BaseModel, ValidationError

from .models import (
    DecisionRecord,
    ExperimentalResult,
    Hypothesis,
    PeptideCandidate,
    Target,
)

ArtifactKind = Literal["target", "hypothesis", "candidate", "experimental_result", "decision_record"]


@dataclass
class ArtifactValidationFailure:
    source: Path
    payload_index: int | None
    artifact_kind: str | None
    message: str


@dataclass
class ValidatedArtifact:
    artifact_kind: str
    source: Path
    payload_index: int | None
    model: BaseModel
    payload: dict[str, Any]


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"


ARTIFACT_MODELS = {
    "target": Target,
    "hypothesis": Hypothesis,
    "candidate": PeptideCandidate,
    "experimental_result": ExperimentalResult,
    "decision_record": DecisionRecord,
}

SCHEMA_FILES = {
    "target": SCHEMA_DIR / "target.schema.json",
    "hypothesis": SCHEMA_DIR / "hypothesis.schema.json",
    "candidate": SCHEMA_DIR / "peptide_candidate.schema.json",
    "experimental_result": SCHEMA_DIR / "experimental_result.schema.json",
    "decision_record": SCHEMA_DIR / "decision_record.schema.json",
}

SCHEMA_REQUIRED_HINTS: dict[str, list[str]] = {
    "target": ["target_id", "name", "organism", "use_case", "rationale"],
    "hypothesis": ["hypothesis_id", "target_id", "claim", "rejection_criteria"],
    "candidate": ["candidate_id", "sequence", "target_id", "hypothesis_id", "modality"],
    "experimental_result": ["result_id", "candidate_id", "result_type"],
    "decision_record": ["decision_id", "campaign_id", "decision", "rationale"],
}

SCHEMA_FIELD_TO_KIND: list[tuple[str, str, set[str]]] = [
    ("candidate", "candidate_id", {"sequence", "target_id", "hypothesis_id", "candidate_id"}),
    ("hypothesis", "hypothesis_id", {"hypothesis_id", "target_id", "claim"}),
    ("target", "target_id", {"target_id", "use_case", "rationale"}),
    ("experimental_result", "result_id", {"result_id", "candidate_id", "result_type"}),
    ("decision_record", "decision_id", {"decision_id", "campaign_id", "decision"}),
]

IDENTIFIER_FIELDS = {
    "target": "target_id",
    "hypothesis": "hypothesis_id",
    "candidate": "candidate_id",
    "experimental_result": "result_id",
    "decision_record": "decision_id",
}


def known_artifact_kinds() -> list[str]:
    return sorted(ARTIFACT_MODELS.keys())


def _read_path_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _iter_json_payloads(path: Path) -> list[tuple[int | None, Any]]:
    text = _read_path_text(path).strip()
    if not text:
        raise ValueError("file is empty.")

    if path.suffix.lower() == ".jsonl":
        entries: list[tuple[int, Any]] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append((line_no, json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL line {line_no}: {exc}") from exc
        return entries

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc

    if isinstance(loaded, list):
        return [(idx, item) for idx, item in enumerate(loaded)]
    return [(None, loaded)]


def _normalize_kind(value: str | None) -> str | None:
    if value is None:
        return None
    if value == "auto":
        return None
    return value.strip().lower()


def _required_fields_from_schema(kind: str) -> list[str]:
    schema_path = SCHEMA_FILES.get(kind)
    if not schema_path or not schema_path.exists():
        return SCHEMA_REQUIRED_HINTS.get(kind, [])

    schema_payload = json.loads(schema_path.read_text(encoding="utf-8"))
    required = schema_payload.get("required")
    if isinstance(required, list):
        return [str(item) for item in required]
    return SCHEMA_REQUIRED_HINTS.get(kind, [])


def _infer_kind(payload: dict[str, Any]) -> str | None:
    payload_keys = set(payload.keys())
    for kind, key_field, required_keys in SCHEMA_FIELD_TO_KIND:
        if required_keys.issubset(payload_keys) and isinstance(payload.get(key_field), str):
            return kind
    return None


def _expand_paths(paths: Sequence[str | Path], recursive: bool) -> list[Path]:
    expanded: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            patterns = ["*.json", "*.jsonl"] if not recursive else ["**/*.json", "**/*.jsonl"]
            for pattern in patterns:
                expanded.extend(sorted(path.glob(pattern)))
        else:
            expanded.append(path)
    return sorted(set(expanded))


def validate_json_artifacts(
    paths: Sequence[str | Path],
    *,
    artifact_kind: str | None = None,
    recursive: bool = False,
    strict: bool = True,
) -> tuple[list[ValidatedArtifact], list[ArtifactValidationFailure]]:
    normalized_kind = _normalize_kind(artifact_kind)
    if normalized_kind is not None and normalized_kind not in ARTIFACT_MODELS:
        raise ValueError(f"Unsupported artifact kind: {artifact_kind}")

    items: list[ValidatedArtifact] = []
    failures: list[ArtifactValidationFailure] = []

    for path in _expand_paths(paths, recursive):
        if not path.exists():
            message = "file not found."
            failures.append(
                ArtifactValidationFailure(
                    source=path,
                    payload_index=None,
                    artifact_kind=normalized_kind,
                    message=message,
                )
            )
            continue
        if path.suffix.lower() not in {".json", ".jsonl"}:
            failures.append(
                ArtifactValidationFailure(
                    source=path,
                    payload_index=None,
                    artifact_kind=normalized_kind,
                    message="unsupported file type; expected .json or .jsonl",
                )
            )
            continue

        try:
            payloads = _iter_json_payloads(path)
        except ValueError as exc:
            failures.append(
                ArtifactValidationFailure(
                    source=path,
                    payload_index=None,
                    artifact_kind=normalized_kind,
                    message=str(exc),
                )
            )
            continue

        for payload_index, payload in payloads:
            payload_errors: list[str] = []
            if not isinstance(payload, dict):
                payload_errors.append("payload must be a JSON object.")
                kind = normalized_kind
            else:
                kind = normalized_kind or _infer_kind(payload)
                if kind is None:
                    payload_errors.append("could not infer artifact kind; use --kind.")
                else:
                    schema_required = _required_fields_from_schema(kind)
                    missing_required = [name for name in schema_required if name not in payload]
                    if missing_required:
                        payload_errors.append(
                            "missing required schema fields: " + ", ".join(sorted(missing_required))
                        )

                    try:
                        model = ARTIFACT_MODELS[kind].model_validate(payload)
                        if not isinstance(payload, dict):
                            payload_errors.append("payload must be an object for model validation.")
                        else:
                            items.append(
                                ValidatedArtifact(
                                    artifact_kind=kind,
                                    source=path,
                                    payload_index=payload_index,
                                    model=model,
                                    payload=payload,
                                )
                            )
                            continue
                    except ValidationError as exc:
                        for error in exc.errors():
                            field_path = ".".join(str(segment) for segment in error.get("loc", ()))
                            msg = error.get("msg", "invalid field")
                            if field_path:
                                payload_errors.append(f"{field_path}: {msg}")
                            else:
                                payload_errors.append(msg)
                    except ValueError as exc:
                        payload_errors.append(str(exc))

            if payload_errors:
                failures.append(
                    ArtifactValidationFailure(
                        source=path,
                        payload_index=payload_index,
                        artifact_kind=kind,
                        message="; ".join(payload_errors),
                    )
                )

    if failures and strict:
        report = [f"{failure.source}:{failure.payload_index}: {failure.message}" for failure in failures]
        raise ValueError("JSON artifact validation failed:\n" + "\n".join(report))

    return items, failures


def artifact_id_from_model(model: BaseModel, kind: str) -> str:
    identifier_field = IDENTIFIER_FIELDS.get(kind)
    if identifier_field is None:
        return "unknown"
    value = getattr(model, identifier_field, None)
    if isinstance(value, str) and value:
        return value
    if isinstance(model.model_dump(mode="json").get(identifier_field), str):
        return str(model.model_dump(mode="json")[identifier_field])
    return "unknown"


def build_validation_report(
    *,
    artifacts: list[ValidatedArtifact],
    failures: list[ArtifactValidationFailure],
    source_paths: Sequence[str | Path] | None = None,
    strict: bool | None = None,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "strict": bool(strict),
        "source_paths": [str(path) for path in (source_paths or [])],
        "valid_count": len(artifacts),
        "invalid_count": len(failures),
        "valid": [
            {
                "artifact_kind": item.artifact_kind,
                "artifact_id": artifact_id_from_model(item.model, item.artifact_kind),
                "source_path": str(item.source),
                "payload_index": item.payload_index,
            }
            for item in artifacts
        ],
        "invalid": [
            {
                "source_path": str(item.source),
                "payload_index": item.payload_index,
                "artifact_kind": item.artifact_kind,
                "message": item.message,
            }
            for item in failures
        ],
    }
