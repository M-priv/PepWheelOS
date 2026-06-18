from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, List, Sequence

from .models import ExperimentalResult
from .storage import append_jsonl, save_json_record


FAILURE_ONTOLOGY: list[str] = [
    "SYN_FAIL_UNKNOWN",
    "SYN_LOW_CRUDE_PURITY",
    "SYN_SEQUENCE_LENGTH_RISK",
    "SYN_HYDROPHOBIC_SEQUENCE",
    "SYN_CYCLISATION_FAILED",
    "SYN_MODIFICATION_FAILED",
    "SYN_LOW_YIELD",
    "SYN_SCALE_UP_FAILED",
    "PURIFICATION_DIFFICULT",
    "COELUTING_IMPURITIES",
    "ANALYTICAL_AMBIGUITY",
    "LCMS_MISMATCH",
    "OXIDATION_PRODUCT",
    "DEAMIDATION_PRODUCT",
    "AGGREGATED_PRODUCT",
    "LOW_AQUEOUS_SOLUBILITY",
    "PRECIPITATION",
    "AGGREGATION",
    "STORAGE_INSTABILITY",
    "FREEZE_THAW_INSTABILITY",
    "BUFFER_INCOMPATIBILITY",
    "NO_BINDING",
    "WEAK_BINDING",
    "NON_SPECIFIC_BINDING",
    "POOR_SELECTIVITY",
    "NO_FUNCTIONAL_EFFECT",
    "ASSAY_INTERFERENCE",
    "OFF_TARGET_SIGNAL",
    "PROTEASE_LABILE",
    "SERUM_INSTABILITY",
    "OXIDATION_LIABILITY",
    "DEAMIDATION_LIABILITY",
    "HYDROLYSIS_LIABILITY",
    "CYTOTOXICITY",
    "IMMUNOGENICITY_RISK",
    "HEMOLYSIS_RISK",
    "POOR_PERMEABILITY",
    "DELIVERY_FAILURE",
    "MODEL_OVERCONFIDENCE",
    "BAD_TARGET_ASSUMPTION",
    "WRONG_BINDING_SITE",
    "DOCKING_ARTEFACT",
    "STRUCTURE_PREDICTION_ARTEFACT",
    "DATA_LEAKAGE",
    "INSUFFICIENT_CONTROLS",
    "AGENT_ORCHESTRATION_FAILURE",
    "MISSING_REPRODUCIBILITY_CONTEXT",
]


_KNOWN_FAILURES = set(FAILURE_ONTOLOGY)
_META_FIELD_MAP = {
    "result id": "result_id",
    "candidate id": "candidate_id",
    "campaign id": "campaign_id",
    "vendor or lab": "vendor_or_lab",
    "result type": "result_type",
}
_SECTION_HEADER_RE = re.compile(r"^\s*##\s*(.+?)\s*$")
_TOP_FIELD_RE = re.compile(r"^\s*([A-Za-z0-9 /_-]+)\s*:\s*(.*)\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(.*)\s*$")
_FAILURE_CODE_RE = re.compile(r"^[A-Z0-9_]{6,}$")


def _normalize_section_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def _normalize_failure_mode(code: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", code.strip().upper().replace("-", "_"))
    return cleaned.replace("__", "_")


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    candidate = re.findall(r"-?\d+(?:\.\d+)?", value.strip())
    if not candidate:
        return None
    try:
        return float(candidate[0])
    except ValueError:
        return None


def _coerce_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    lowered = value.lower()
    if lowered in {"na", "n/a", "-", "none", "null"}:
        return None
    parsed_float = _as_float(value)
    if parsed_float is not None:
        return parsed_float
    return value


def _extract_failure_mode_lines(lines: Sequence[str]) -> tuple[list[str], list[str]]:
    explicit: list[str] = []
    unknown: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = _LIST_ITEM_RE.match(line)
        if m:
            line = m.group(1).strip()
        if not _FAILURE_CODE_RE.match(_normalize_failure_mode(line)):
            # The section often contains explanatory prose; only structured tokens
            # are treated as machine-validated failure codes.
            continue
        if not line or line.lower().startswith("to be populated"):
            continue
        code = _normalize_failure_mode(line)
        if code in _KNOWN_FAILURES:
            explicit.append(code)
        else:
            unknown.append(code)
    return explicit, unknown


def _parse_key_values(lines: Sequence[str]) -> dict[str, Any]:
    key_values: dict[str, Any] = {}
    for raw in lines:
        if "|" not in raw:
            continue
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        metric = cells[0].strip()
        value = cells[1].strip()
        lower = metric.lower().replace(" ", "")
        if not metric or lower in {"metric", "value", "notes", "---"}:
            continue
        if set(metric) == {"-"} or set(lower) <= {"-"}:
            continue
        parsed = _coerce_scalar(value)
        if parsed is not None:
            key_values[metric] = parsed
    return key_values


def _normalise_metric_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _read_metric_by_alias(key_values: dict[str, Any], aliases: Sequence[str]) -> float | None:
    alias_set = {_normalise_metric_key(alias) for alias in aliases}
    for raw_key, raw_value in key_values.items():
        normalised_key = _normalise_metric_key(raw_key)
        if normalised_key not in alias_set:
            continue
        value = _as_float(raw_value) if isinstance(raw_value, str) else _as_float(str(raw_value))
        if value is not None:
            return value
    return None


def _has_text(text: str, keyword: str) -> bool:
    return keyword in text


def parse_experimental_result_text(
    text: str,
    *,
    source_path: Path | None = None,
    strict: bool = True,
) -> ExperimentalResult:
    raw_text = (text or "").strip()
    if not raw_text:
        raise ValueError("Result text is empty.")

    metadata: dict[str, str] = {}
    sections: dict[str, list[str]] = {
        "summary": [],
        "interpretation": [],
        "failure_modes": [],
        "next_design_recommendation": [],
        "key_values": [],
    }
    section: str | None = None

    for line in raw_text.splitlines():
        section_match = _SECTION_HEADER_RE.match(line)
        if section_match:
            section = _normalize_section_name(section_match.group(1))
            continue

        metadata_match = _TOP_FIELD_RE.match(line)
        if metadata_match and section is None:
            key = metadata_match.group(1).strip().lower()
            value = metadata_match.group(2).strip()
            canonical = _META_FIELD_MAP.get(key)
            if canonical:
                metadata[canonical] = value
            continue

        normalized_section = section
        if normalized_section in sections:
            line_text = line.strip()
            if line_text:
                sections[normalized_section].append(line_text)

    if "result_id" not in metadata:
        raise ValueError("Result metadata missing required field: Result ID.")
    if "candidate_id" not in metadata:
        raise ValueError("Result metadata missing required field: Candidate ID.")
    if "result_type" not in metadata:
        raise ValueError("Result metadata missing required field: Result type.")

    explicit, unknown = _extract_failure_mode_lines(sections["failure_modes"])
    if strict and unknown:
        raise ValueError(
            f"Unknown failure modes in {metadata['result_id']}: {', '.join(unknown)}"
        )

    key_values = _parse_key_values(sections["key_values"])
    summary = "\n".join(sections["summary"]).strip() or "No summary provided."
    interpretation = (
        "\n".join(sections["interpretation"]).strip() or "No interpretation provided."
    )
    next_action = "\n".join(sections["next_design_recommendation"]).strip()
    raw_file_refs: list[str] = []
    if source_path is not None:
        raw_file_refs.append(str(source_path))

    return ExperimentalResult(
        result_id=metadata["result_id"],
        candidate_id=metadata["candidate_id"],
        result_type=metadata["result_type"],
        summary=summary,
        interpretation=interpretation,
        vendor_or_lab=metadata.get("vendor_or_lab") or None,
        raw_file_refs=raw_file_refs,
        key_values=key_values,
        failure_modes=explicit,
        next_action=next_action,
    )


def parse_experimental_result_file(
    path: str | Path,
    *,
    strict: bool = True,
) -> ExperimentalResult:
    source = Path(path)
    payload = source.read_text(encoding="utf-8").strip()
    if not payload:
        raise ValueError(f"Result file is empty: {source}")

    if payload.startswith("{"):
        raw = json.loads(payload)
        result = ExperimentalResult.model_validate(raw)
        if source is not None:
            result.raw_file_refs.append(str(source))
        if strict:
            unknown = [
                mode
                for mode in result.failure_modes
                if _normalize_failure_mode(str(mode)) not in _KNOWN_FAILURES
            ]
            if unknown:
                raise ValueError(
                    f"Unknown failure modes in {result.result_id}: {', '.join(map(str, unknown))}"
                )
        return result

    return parse_experimental_result_text(payload, source_path=source, strict=strict)


def classify_failure_modes(
    result: ExperimentalResult,
    *,
    strict: bool = True,
) -> list[str]:
    discovered: list[str] = []
    discovered_set = set[str]()

    def _add(mode: str) -> None:
        if mode not in discovered_set and mode in _KNOWN_FAILURES:
            discovered.append(mode)
            discovered_set.add(mode)

    for mode in result.failure_modes:
        normalized = _normalize_failure_mode(mode)
        if normalized in _KNOWN_FAILURES:
            _add(normalized)
        elif strict:
            raise ValueError(f"Unknown failure mode in manual input: {mode}")

    narrative = f"{result.summary} {result.interpretation}".lower()
    values = {_normalise_metric_key(k): _as_float(v) for k, v in result.key_values.items()}

    yield_value = _read_metric_by_alias(values, ["yield", "crude_yield", "recovery", "synthesis_yield"])
    if yield_value is not None and yield_value < 20:
        _add("SYN_LOW_YIELD")

    purity = _read_metric_by_alias(values, ["purity", "crude_purity", "final_purity"])
    if purity is not None and purity < 90:
        _add("SYN_LOW_CRUDE_PURITY")

    solubility = _read_metric_by_alias(
        values,
        ["solubility", "aqueous_solubility", "solubility_mg_ml", "solubility_mgml"],
    )
    if solubility is not None and solubility < 0.5:
        _add("LOW_AQUEOUS_SOLUBILITY")

    if _has_text(narrative, "no measurable activity") or _has_text(narrative, "no antimicrobial activity") or _has_text(narrative, "no binding"):
        _add("NO_BINDING")
    if "weak activity" in narrative or "low activity" in narrative or "modest activity" in narrative:
        _add("WEAK_BINDING")
    if "non-specific" in narrative or "nonspecific" in narrative:
        _add("NON_SPECIFIC_BINDING")
    if "poor selectivity" in narrative:
        _add("POOR_SELECTIVITY")
    if "off-target" in narrative:
        _add("OFF_TARGET_SIGNAL")
    if "no functional effect" in narrative:
        _add("NO_FUNCTIONAL_EFFECT")
    if "assay interference" in narrative or "high background" in narrative or "interference" in narrative:
        _add("ASSAY_INTERFERENCE")

    if "synthesis failed" in narrative:
        _add("SYN_FAIL_UNKNOWN")
    if "hydrophobic sequence" in narrative or "hydrophobicity" in narrative:
        _add("SYN_HYDROPHOBIC_SEQUENCE")
    if "cyclisation" in narrative or "cyclization" in narrative:
        _add("SYN_CYCLISATION_FAILED")
    if "modification failed" in narrative:
        _add("SYN_MODIFICATION_FAILED")
    if "scale-up" in narrative:
        _add("SYN_SCALE_UP_FAILED")
    if "difficult purification" in narrative or "difficult to purify" in narrative:
        _add("PURIFICATION_DIFFICULT")
    if "co-eluting" in narrative or "coeluting" in narrative:
        _add("COELUTING_IMPURITIES")
    if "analytical ambiguity" in narrative or "lcm sm ambiguous" in narrative:
        _add("ANALYTICAL_AMBIGUITY")
    if "lcm s mismatch" in narrative or "lcms mismatch" in narrative:
        _add("LCMS_MISMATCH")
    if "oxidized" in narrative or "oxidation" in narrative:
        _add("OXIDATION_PRODUCT")
    if "deamidated" in narrative or "deamidation" in narrative:
        _add("DEAMIDATION_PRODUCT")
    if "aggregated product" in narrative or "aggregate" in narrative:
        _add("AGGREGATED_PRODUCT")
        _add("AGGREGATION")
    if "precipitation" in narrative or "precipitated" in narrative:
        _add("PRECIPITATION")
    if "storage instability" in narrative:
        _add("STORAGE_INSTABILITY")
    if "freeze-thaw" in narrative or "freeze thaw" in narrative:
        _add("FREEZE_THAW_INSTABILITY")
    if "buffer" in narrative and ("incompatibility" in narrative or "failed condition" in narrative):
        _add("BUFFER_INCOMPATIBILITY")

    if "protease" in narrative:
        _add("PROTEASE_LABILE")
    if "serum instability" in narrative or "serum degradation" in narrative:
        _add("SERUM_INSTABILITY")
    if "cytotoxic" in narrative:
        _add("CYTOTOXICITY")
    if "hemolysis" in narrative:
        _add("HEMOLYSIS_RISK")
    if "immunogenic" in narrative:
        _add("IMMUNOGENICITY_RISK")
    if "permeability" in narrative:
        _add("POOR_PERMEABILITY")
    if "delivery failure" in narrative:
        _add("DELIVERY_FAILURE")

    if "model overpredict" in narrative or "model over-confident" in narrative or "overconfident" in narrative:
        _add("MODEL_OVERCONFIDENCE")
    if "wrong target" in narrative or "target mismatch" in narrative:
        _add("WRONG_BINDING_SITE")
    if "docking artefact" in narrative or "docking artifact" in narrative:
        _add("DOCKING_ARTEFACT")
    if "structure prediction artefact" in narrative or "structure prediction artifact" in narrative:
        _add("STRUCTURE_PREDICTION_ARTEFACT")
    if "data leakage" in narrative:
        _add("DATA_LEAKAGE")
    if "insufficient controls" in narrative or "control was missing" in narrative:
        _add("INSUFFICIENT_CONTROLS")
    if "agent orchestration" in narrative:
        _add("AGENT_ORCHESTRATION_FAILURE")
    if "inconsistent" in narrative or "not reproducible" in narrative:
        _add("MISSING_REPRODUCIBILITY_CONTEXT")
    if "bad controls" in narrative:
        _add("MISSING_REPRODUCIBILITY_CONTEXT")

    if "no controls" in narrative:
        _add("INSUFFICIENT_CONTROLS")

    if "bad sequence length" in narrative or "length risk" in narrative:
        _add("SYN_SEQUENCE_LENGTH_RISK")

    if not discovered:
        return []
    return discovered


def ingest_simulated_results(
    result_paths: Iterable[str | Path],
    output_dir: str | Path | None = None,
    *,
    strict: bool = True,
    classify: bool = True,
) -> tuple[list[ExperimentalResult], list[str]]:
    results: list[ExperimentalResult] = []
    parse_errors: list[str] = []
    output_root = Path(output_dir) if output_dir is not None else None
    seen_ids: set[str] = set()
    records_dir: Path | None = None
    events_path: Path | None = None
    if output_root is not None:
        output_root.mkdir(parents=True, exist_ok=True)
        records_dir = output_root / "records"
        records_dir.mkdir(parents=True, exist_ok=True)
        events_path = output_root / "experimental_results.jsonl"

    for path in result_paths:
        try:
            result = parse_experimental_result_file(path, strict=strict)
            if classify:
                result.failure_modes = classify_failure_modes(result, strict=strict)
            if result.result_id in seen_ids:
                message = f"Duplicate result_id encountered: {result.result_id}"
                if strict:
                    raise ValueError(message)
                parse_errors.append(message)
                continue
            seen_ids.add(result.result_id)
            if records_dir is not None:
                save_json_record(result, records_dir / f"{result.result_id}.json")
            if events_path is not None:
                append_jsonl(result, events_path)
            results.append(result)
        except ValueError as exc:
            if strict:
                raise
            parse_errors.append(f"{path}: {exc}")

    return results, parse_errors


def failure_mode_counts(results: Sequence[ExperimentalResult]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for result in results:
        for mode in classify_failure_modes(result, strict=False):
            counter[mode] += 1
    return dict(counter)
