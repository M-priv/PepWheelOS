from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import re
from typing import Any, Dict, List, Sequence


AMINO_STANDARD = set("ACDEFGHIKLMNPQRSTVWY")
AMINO_AMBIGUOUS = set("BJOUXZ")
VALID_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class ValidationEvent:
    severity: str
    code: str
    message: str
    row: int | None = None
    row_id: str | None = None
    location: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "row": self.row,
            "row_id": self.row_id,
            "location": self.location,
            "metadata": self.metadata,
        }

    @property
    def as_text(self) -> str:
        prefix = self.code
        if self.row is not None:
            prefix = f"{prefix} (row {self.row})"
        if self.row_id:
            prefix = f"{prefix} [{self.row_id}]"
        return f"{self.severity.upper()}: {prefix} - {self.message}"


@dataclass(frozen=True)
class SplitManifest:
    dataset_id: str
    split_method: str
    split_column: str
    split_required: bool = True
    split_tags: List[str] = field(default_factory=list)
    homology_guard: Dict[str, Any] = field(default_factory=dict)
    dataset_version: str | None = None
    source_reference: str | None = None
    notes: str | None = None
    created_at: str | None = None
    generated_by: str | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def split_tags_set(self) -> set[str]:
        return set(self.split_tags)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "split_method": self.split_method,
            "split_column": self.split_column,
            "split_required": self.split_required,
            "split_tags": self.split_tags,
            "homology_guard": self.homology_guard,
            "dataset_version": self.dataset_version,
            "source_reference": self.source_reference,
            "notes": self.notes,
            "created_at": self.created_at,
            "generated_by": self.generated_by,
            "extra": self.extra,
        }


@dataclass(frozen=True)
class DataGovernancePreflightResult:
    dataset_path: Path
    records: List[Dict[str, Any]]
    split_distribution: Dict[str, int]
    events: List[ValidationEvent]
    manifest: SplitManifest | None = None
    manifest_path: Path | None = None
    validated_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    @property
    def error_count(self) -> int:
        return sum(1 for event in self.events if event.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for event in self.events if event.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for event in self.events if event.severity == "info")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "dataset_path": str(self.dataset_path),
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "validated_at": self.validated_at,
            "record_count": len(self.records),
            "split_distribution": self.split_distribution,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "manifest": self.manifest.as_dict() if self.manifest else None,
            "events": [event.to_dict() for event in self.events],
        }


def _event(
    *, severity: str, code: str, message: str, **kwargs: Any
) -> ValidationEvent:
    return ValidationEvent(severity=severity, code=code, message=message, **kwargs)


def _normalise_sequence(sequence: str) -> str:
    if sequence is None:
        return ""
    return str(sequence).strip().replace(" ", "").upper()


def _normalize_id(value: str) -> str:
    return (value or "").strip()


def _validate_id(value: str) -> tuple[bool, str | None]:
    if not value:
        return False, "required identifier is missing"
    if not VALID_ID_PATTERN.match(value):
        return False, "identifier contains unsupported characters"
    return True, None


def _sequence_validation_errors(
    sequence: str, allow_ambiguous_residues: bool
) -> tuple[bool, str | None, List[str]]:
    if not sequence:
        return False, "sequence is required", []

    valid_residues = AMINO_STANDARD | AMINO_AMBIGUOUS
    unknown = sorted(set(sequence) - valid_residues)
    if unknown:
        return False, "sequence contains unknown residues", [" ".join(unknown)]

    warnings: List[str] = []
    ambiguous_residues = sorted(set(sequence) & AMINO_AMBIGUOUS)
    if ambiguous_residues and allow_ambiguous_residues:
        warnings.append("".join(ambiguous_residues))
    elif ambiguous_residues:
        return False, "sequence contains unsupported ambiguous residues", ["".join(ambiguous_residues)]

    return True, None, warnings


def _one_indel_similarity(seq_a: str, seq_b: str) -> float:
    if not seq_a or not seq_b:
        return 0.0
    if len(seq_a) > len(seq_b):
        seq_a, seq_b = seq_b, seq_a

    best = 0
    for shift in (0, 1):
        mismatches = 0
        for i, aa in enumerate(seq_a):
            if aa != seq_b[i + shift]:
                mismatches += 1
        match_ratio = 1.0 - (mismatches / len(seq_b))
        best = max(best, match_ratio)
    return best


def _sequence_similarity(seq_a: str, seq_b: str) -> float:
    len_a = len(seq_a)
    len_b = len(seq_b)
    if not len_a or not len_b:
        return 0.0
    if abs(len_a - len_b) > 1:
        return 0.0

    if len_a == len_b:
        mismatches = sum(aa != bb for aa, bb in zip(seq_a, seq_b))
        return 1.0 - (mismatches / len_a)
    return _one_indel_similarity(seq_a, seq_b)


def load_split_manifest(
    path: str | Path,
) -> tuple[SplitManifest | None, List[ValidationEvent]]:
    events: List[ValidationEvent] = []
    manifest_path = Path(path)
    if not manifest_path.exists():
        events.append(
            _event(
                severity="error",
                code="SPLIT_MANIFEST_NOT_FOUND",
                message=f"split manifest file does not exist: {manifest_path}",
                location=str(manifest_path),
            )
        )
        return None, events

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        events.append(
            _event(
                severity="error",
                code="SPLIT_MANIFEST_PARSE_ERROR",
                message=f"could not parse split manifest: {exc}",
                location=str(manifest_path),
            )
        )
        return None, events

    if not isinstance(raw, dict):
        events.append(
            _event(
                severity="error",
                code="SPLIT_MANIFEST_INVALID_FORMAT",
                message="split manifest must be a JSON object",
                location=str(manifest_path),
            )
        )
        return None, events

    required = ("dataset_id", "split_method", "split_column")
    missing = [key for key in required if key not in raw]
    if missing:
        events.append(
            _event(
                severity="error",
                code="SPLIT_MANIFEST_MISSING_FIELDS",
                message=f"split manifest missing required fields: {', '.join(missing)}",
                location=str(manifest_path),
                metadata={"missing": missing},
            )
        )
        return None, events

    split_tags = raw.get("split_tags") or []
    if split_tags and not isinstance(split_tags, list):
        events.append(
            _event(
                severity="error",
                code="SPLIT_MANIFEST_INVALID_SPLIT_TAGS",
                message="split_tags must be a JSON list",
                location=str(manifest_path),
            )
        )
        split_tags = []

    split_required = bool(raw.get("split_required", True))
    homology_guard = raw.get("homology_guard") or {}
    if not isinstance(homology_guard, dict):
        events.append(
            _event(
                severity="error",
                code="SPLIT_MANIFEST_INVALID_GUARD",
                message="homology_guard must be an object",
                location=str(manifest_path),
            )
        )
        homology_guard = {}

    return (
        SplitManifest(
            dataset_id=str(raw["dataset_id"]),
            split_method=str(raw["split_method"]),
            split_column=str(raw["split_column"]),
            split_required=split_required,
            split_tags=[str(item) for item in split_tags],
            homology_guard=homology_guard,
            dataset_version=raw.get("dataset_version"),
            source_reference=raw.get("source_reference"),
            notes=raw.get("notes"),
            created_at=raw.get("created_at"),
            generated_by=raw.get("generated_by"),
            extra={
                key: value
                for key, value in raw.items()
                if key
                not in {
                    "dataset_id",
                    "split_method",
                    "split_column",
                    "split_required",
                    "split_tags",
                    "homology_guard",
                    "dataset_version",
                    "source_reference",
                    "notes",
                    "created_at",
                    "generated_by",
                }
            },
        ),
        events,
    )


def validate_dataset_ingestion(
    *,
    dataset_path: str | Path,
    required_columns: Sequence[str] | None = None,
    sequence_column: str = "sequence",
    id_column: str = "peptide_id",
    split_column: str | None = None,
    allow_ambiguous_residues: bool = True,
) -> tuple[List[Dict[str, Any]], List[ValidationEvent], Dict[str, int]]:
    dataset_path = Path(dataset_path)
    events: List[ValidationEvent] = []
    rows: List[Dict[str, Any]] = []
    split_distribution: Dict[str, int] = defaultdict(int)

    if required_columns is None:
        required_columns = [id_column, sequence_column]

    if not dataset_path.exists():
        events.append(
            _event(
                severity="error",
                code="DATASET_NOT_FOUND",
                message=f"dataset file does not exist: {dataset_path}",
                location=str(dataset_path),
            )
        )
        return rows, events, split_distribution

    try:
        with dataset_path.open("r", encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            header = reader.fieldnames or []
            for required in required_columns:
                if required not in header:
                    events.append(
                        _event(
                            severity="error",
                            code="DATASET_MISSING_REQUIRED_COLUMN",
                            message=f"missing required column: {required}",
                            location="header",
                        )
                    )

            seen_ids: Dict[str, int] = {}
            for row_number, row in enumerate(reader, start=2):
                if not row:
                    events.append(
                        _event(
                            severity="warning",
                            code="DATASET_EMPTY_ROW",
                            message="empty row encountered",
                            row=row_number,
                        )
                    )
                    continue

                normalised_row: Dict[str, Any] = {
                    key: (value.strip() if isinstance(value, str) else value)
                    for key, value in row.items()
                }

                row_id = _normalize_id(normalised_row.get(id_column, ""))
                normalised_row[id_column] = row_id
                sequence = _normalise_sequence(normalised_row.get(sequence_column, ""))
                normalised_row[sequence_column] = sequence

                if row_id in seen_ids:
                    events.append(
                        _event(
                            severity="error",
                            code="DATASET_DUPLICATE_ID",
                            message="duplicate row identifier",
                            row=row_number,
                            row_id=row_id,
                            metadata={"previous_row": seen_ids[row_id]},
                        )
                    )
                else:
                    seen_ids[row_id] = row_number

                id_ok, id_error = _validate_id(row_id)
                if not id_ok:
                    events.append(
                        _event(
                            severity="error",
                            code="DATASET_INVALID_ID",
                            message=id_error or "invalid id",
                            row=row_number,
                            row_id=row_id,
                        )
                    )

                sequence_ok, seq_error, seq_warns = _sequence_validation_errors(
                    sequence, allow_ambiguous_residues=allow_ambiguous_residues
                )
                if not sequence_ok:
                    events.append(
                        _event(
                            severity="error",
                            code="DATASET_INVALID_SEQUENCE",
                            message=seq_error or "invalid sequence",
                            row=row_number,
                            row_id=row_id,
                            metadata={"sequence": sequence, "details": seq_warns},
                        )
                    )
                for residue in seq_warns:
                    events.append(
                        _event(
                            severity="warning",
                            code="DATASET_AMBIGUOUS_RESIDUES",
                            message="ambiguous residues present",
                            row=row_number,
                            row_id=row_id,
                            metadata={"residues": residue},
                        )
                    )

                if split_column:
                    split_value = normalised_row.get(split_column, "") or ""
                    split_value = str(split_value).strip()
                    split_distribution[split_value] += 1
                    normalised_row[split_column] = split_value
                normalised_row["_row_number"] = row_number

                rows.append(normalised_row)
    except OSError as exc:
        events.append(
            _event(
                severity="error",
                code="DATASET_READ_ERROR",
                message=f"unable to read dataset: {exc}",
                location=str(dataset_path),
            )
        )
        return rows, events, split_distribution

    if not rows:
        events.append(
            _event(
                severity="warning",
                code="DATASET_EMPTY",
                message="dataset loaded with no records",
                location=str(dataset_path),
            )
        )

    return rows, events, dict(split_distribution)


def run_split_and_leakage_checks(
    *,
    rows: Sequence[Dict[str, Any]],
    split_column: str | None,
    split_tags: Sequence[str] | None,
    sequence_column: str = "sequence",
    id_column: str = "peptide_id",
    near_duplicate_threshold: float = 0.95,
    max_pairs: int = 25000,
    strict: bool = False,
) -> List[ValidationEvent]:
    events: List[ValidationEvent] = []

    split_set = set(split_tags or [])
    exact_seen: Dict[str, List[dict[str, Any]]] = defaultdict(list)
    fingerprint_buckets: Dict[tuple[int, str, str], List[dict[str, Any]]] = defaultdict(list)
    pair_checks = 0

    for row in rows:
        split_value = row.get(split_column or "", "") if split_column else ""
        row_id = row.get(id_column, "")
        sequence = row.get(sequence_column, "") or ""
        row_number = row.get("_row_number")

        if split_column and split_set and split_value and split_value not in split_set:
            events.append(
                _event(
                    severity="error",
                    code="DATASET_SPLIT_TAG_MISMATCH",
                    message=f"split value '{split_value}' not in split manifest tags",
                    row_id=row_id,
                    metadata={"allowed": list(split_set)},
                )
            )

        previous = exact_seen.get(sequence, [])
        for prior in previous:
            if prior["split"] != split_value:
                events.append(
                    _event(
                        severity="error",
                        code="SPLIT_LEAKAGE_EXACT_SEQUENCE",
                        message="exact sequence observed across multiple splits",
                        row=row_number,
                        row_id=row_id,
                        metadata={
                            "sequence": sequence,
                            "prior_row": prior["row"],
                            "prior_id": prior["id"],
                        },
                    )
                )
        exact_seen[sequence].append(
            {"split": split_value, "id": row_id, "row": row_number, "sequence": sequence}
        )

        fingerprint = (len(sequence), sequence[:3], sequence[-3:])
        bucket = fingerprint_buckets[fingerprint]
        for prior in bucket:
            if pair_checks >= max_pairs:
                events.append(
                    _event(
                        severity="warning",
                        code="SPLIT_LEAKAGE_PAIRWISE_TRUNCATED",
                        message=f"near-duplicate search truncated at {max_pairs} pairs",
                    )
                )
                return events

            pair_checks += 1
            if prior["split"] == split_value:
                continue
            similarity = _sequence_similarity(sequence, prior["sequence"])
            if similarity >= near_duplicate_threshold:
                severity = "error" if strict else "warning"
                events.append(
                    _event(
                        severity=severity,
                        code="SPLIT_LEAKAGE_NEAR_DUPLICATE",
                        message=(
                            f"high similarity near-duplicate sequence detected (score "
                            f"{similarity:.3f})"
                        ),
                        row_id=row_id,
                        metadata={
                            "sequence": sequence,
                            "other_sequence": prior["sequence"],
                            "similarity": similarity,
                            "split": split_value,
                            "other_split": prior["split"],
                            "row": row_number,
                            "other_row": prior["row"],
                        },
                    )
                )
        bucket.append(
            {"sequence": sequence, "split": split_value, "id": row_id, "row": row_number}
        )

    return events


def run_data_governance_preflight(
    *,
    dataset_csv_path: str | Path,
    split_manifest_path: str | Path | None = None,
    required_columns: Sequence[str] | None = None,
    strict: bool = True,
    allow_ambiguous_residues: bool = True,
    near_duplicate_threshold: float = 0.95,
    max_near_duplicate_pairs: int = 25000,
) -> DataGovernancePreflightResult:
    split_manifest: SplitManifest | None = None
    split_manifest_events: List[ValidationEvent] = []
    split_col = None
    split_tags: List[str] = []

    if split_manifest_path:
        manifest, split_manifest_events = load_split_manifest(split_manifest_path)
        if manifest:
            split_manifest = manifest
            split_col = manifest.split_column
            split_tags = manifest.split_tags
    else:
        split_col = None
        split_tags = []

    base_contract_columns = (
        list(required_columns)
        if required_columns is not None
        else ["peptide_id", "sequence"]
    )
    required_contract_columns = base_contract_columns[:]
    if split_manifest and split_manifest.split_required and split_col:
        if split_col not in required_contract_columns:
            required_contract_columns.append(split_col)

    rows, contract_events, split_distribution = validate_dataset_ingestion(
        dataset_path=dataset_csv_path,
        required_columns=required_contract_columns,
        split_column=split_col,
        allow_ambiguous_residues=allow_ambiguous_residues,
    )

    if split_col:
        has_non_empty_split = any(value for value in split_distribution if value)
        if not has_non_empty_split:
            split_required = split_manifest.split_required if split_manifest else False
            split_manifest_events.append(
                _event(
                    severity="error" if split_required else "warning",
                    code="DATASET_SPLIT_MISSING_VALUES",
                    message=f"split column '{split_col}' present but empty for all rows",
                    location=split_col,
                )
            )
        unknown_tags = [
            tag for tag in split_distribution if tag and tag not in set(split_tags)
        ]
        for tag in unknown_tags:
            split_manifest_events.append(
                _event(
                    severity="warning",
                    code="DATASET_UNLISTED_SPLIT_TAG",
                    message=f"split value '{tag}' not listed in manifest split tags",
                    location=split_col,
                    metadata={"manifest": split_tags},
                )
            )
    elif split_col is None:
        split_manifest_events.append(
            _event(
                severity="info",
                code="DATASET_NO_SPLIT_COLUMN",
                message="dataset has no configured split column; split-level leakage checks limited",
                location="preflight",
            )
        )

    leakage_events = run_split_and_leakage_checks(
        rows=rows,
        split_column=split_col,
        split_tags=split_tags if split_col else None,
        near_duplicate_threshold=near_duplicate_threshold,
        max_pairs=max_near_duplicate_pairs,
        strict=strict,
    )

    events = [*split_manifest_events, *contract_events, *leakage_events]

    if strict:
        for event in events:
            if event.severity == "error":
                raise ValueError(
                    f"Data governance preflight failed for dataset '{dataset_csv_path}'. "
                    f"{sum(e.severity == 'error' for e in events)} error(s)."
                )

    return DataGovernancePreflightResult(
        dataset_path=Path(dataset_csv_path),
        records=rows,
        split_distribution=dict(split_distribution),
        events=events,
        manifest=split_manifest,
        manifest_path=Path(split_manifest_path) if split_manifest_path else None,
    )
