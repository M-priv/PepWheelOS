from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from .active_learning import ActiveLearningScoringSummaryOutput
from .prompt_pipeline import (
    AssayPackOutput,
    CandidateCardOutput,
    PromptPacket,
    RedTeamOutput,
    TargetDossierOutput,
)


CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "target_dossier": TargetDossierOutput,
    "candidate_card": CandidateCardOutput,
    "red_team_review": RedTeamOutput,
    "assay_pack": AssayPackOutput,
    "active_learning_scoring_summary": ActiveLearningScoringSummaryOutput,
}


RETRYABLE_FAILURE_CODES = {
    "EMPTY_OUTPUT",
    "NON_JSON_OUTPUT",
    "NON_OBJECT_OUTPUT",
    "UNSUPPORTED_ARTIFACT_CONTRACT",
    "SCHEMA_VALIDATION_FAILED",
    "CONTEXT_ID_MISMATCH",
}


@dataclass
class AgentRetryPolicy:
    max_attempts: int = 3
    retryable_failure_codes: set[str] = field(
        default_factory=lambda: set(RETRYABLE_FAILURE_CODES)
    )
    require_human_review_after_exhaustion: bool = True

    def should_retry(self, *, attempt: int, failure_codes: list[str]) -> bool:
        if attempt >= self.max_attempts:
            return False
        return any(code in self.retryable_failure_codes for code in failure_codes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "retryable_failure_codes": sorted(self.retryable_failure_codes),
            "require_human_review_after_exhaustion": self.require_human_review_after_exhaustion,
        }


@dataclass
class AgentContractEvaluation:
    packet_id: str
    artifact: str
    attempt: int
    passed: bool
    failure_codes: list[str]
    errors: list[str]
    warnings: list[str]
    parsed_payload: dict[str, Any] | None
    validated_payload: dict[str, Any] | None
    retry_recommended: bool
    retry_packet: PromptPacket | None = None
    evaluated_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "artifact": self.artifact,
            "attempt": self.attempt,
            "passed": self.passed,
            "failure_codes": self.failure_codes,
            "errors": self.errors,
            "warnings": self.warnings,
            "parsed_payload": self.parsed_payload,
            "validated_payload": self.validated_payload,
            "retry_recommended": self.retry_recommended,
            "retry_packet": self.retry_packet.model_dump() if self.retry_packet else None,
            "evaluated_at": self.evaluated_at,
        }


def load_prompt_packet(path: str | Path) -> PromptPacket:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return PromptPacket(
        packet_id=str(payload["packet_id"]),
        agent=str(payload["agent"]),
        artifact=str(payload["artifact"]),
        instruction=str(payload["instruction"]),
        input_payload=dict(payload["input_payload"]),
        output_schema=dict(payload["output_schema"]),
        created_at=str(payload.get("created_at", "")),
    )


def _parse_json_object(raw_output: str) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    errors: list[str] = []
    failure_codes: list[str] = []
    text = raw_output.strip()
    if not text:
        return None, ["EMPTY_OUTPUT"], ["Agent output was empty."]
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, ["NON_JSON_OUTPUT"], [f"Agent output was not valid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, ["NON_OBJECT_OUTPUT"], ["Agent output must be a single JSON object."]
    return payload, failure_codes, errors


def _expected_context_ids(packet: PromptPacket) -> dict[str, str]:
    source = packet.input_payload
    expected: dict[str, str] = {}
    if isinstance(source.get("target"), dict) and source["target"].get("target_id"):
        expected["target_id"] = str(source["target"]["target_id"])
    if isinstance(source.get("hypothesis"), dict) and source["hypothesis"].get("hypothesis_id"):
        expected["hypothesis_id"] = str(source["hypothesis"]["hypothesis_id"])
    if isinstance(source.get("candidate"), dict) and source["candidate"].get("candidate_id"):
        expected["candidate_id"] = str(source["candidate"]["candidate_id"])
    if source.get("campaign_id"):
        expected["campaign_id"] = str(source["campaign_id"])
    if source.get("run_id"):
        expected["run_id"] = str(source["run_id"])
    return expected


def _check_context_ids(packet: PromptPacket, payload: dict[str, Any]) -> list[str]:
    expected = _expected_context_ids(packet)
    errors: list[str] = []
    for field_name, expected_value in expected.items():
        observed_value = payload.get(field_name)
        if observed_value is None:
            continue
        if str(observed_value) != expected_value:
            errors.append(
                f"{field_name} mismatch: expected {expected_value}, observed {observed_value}."
            )

    if packet.artifact == "active_learning_scoring_summary":
        selected = set(str(item) for item in packet.input_payload.get("selected_candidate_ids", []))
        observed = set(str(item) for item in payload.get("selected_candidate_ids", []))
        unexpected = sorted(observed - selected)
        if unexpected:
            errors.append(
                "selected_candidate_ids contains ids outside the active-learning plan: "
                + ", ".join(unexpected)
            )
    return errors


def _audit_warnings(packet: PromptPacket, payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if packet.artifact == "target_dossier":
        if not payload.get("unknowns"):
            warnings.append("target_dossier should record unknowns or unresolved evidence gaps.")
        if not payload.get("risks"):
            warnings.append("target_dossier should record risks.")
    elif packet.artifact == "candidate_card":
        if not payload.get("risk_flags"):
            warnings.append("candidate_card has no risk flags; verify this is intentional.")
        if payload.get("manufacturability_score") is None:
            warnings.append("candidate_card omitted manufacturability_score.")
    elif packet.artifact == "red_team_review":
        if not payload.get("failure_hypotheses"):
            warnings.append("red_team_review should include failure_hypotheses.")
        if not payload.get("evidence_required"):
            warnings.append("red_team_review should include evidence_required.")
    elif packet.artifact == "assay_pack":
        if not payload.get("controls"):
            warnings.append("assay_pack should include controls.")
        if not payload.get("rejection_criteria"):
            warnings.append("assay_pack should include rejection_criteria.")
    elif packet.artifact == "active_learning_scoring_summary":
        if not payload.get("uncertainty_notes"):
            warnings.append("active_learning_scoring_summary should include uncertainty_notes.")
    return warnings


def _retry_instruction(
    *,
    original_packet: PromptPacket,
    failure_codes: list[str],
    errors: list[str],
    warnings: list[str],
    attempt: int,
) -> str:
    issue_lines = [f"- ERROR: {message}" for message in errors]
    issue_lines.extend(f"- WARNING: {message}" for message in warnings)
    issues = "\n".join(issue_lines) if issue_lines else "- No detailed issue captured."
    return (
        f"Repair the previous {original_packet.artifact} output for packet "
        f"{original_packet.packet_id}. This is retry attempt {attempt + 1}. "
        "Return strictly one JSON object and no prose. Preserve all source identifiers "
        "from input_payload. Satisfy the output_schema exactly and address these issues:\n"
        f"{issues}\n"
        f"Failure codes: {', '.join(failure_codes) or 'none'}."
    )


def build_retry_packet(
    *,
    original_packet: PromptPacket,
    failure_codes: list[str],
    errors: list[str],
    warnings: list[str],
    attempt: int,
) -> PromptPacket:
    return PromptPacket(
        packet_id=f"{original_packet.packet_id}-retry-{attempt + 1}",
        agent=original_packet.agent,
        artifact=original_packet.artifact,
        instruction=_retry_instruction(
            original_packet=original_packet,
            failure_codes=failure_codes,
            errors=errors,
            warnings=warnings,
            attempt=attempt,
        ),
        input_payload={
            **original_packet.input_payload,
            "previous_packet_id": original_packet.packet_id,
            "retry_attempt": attempt + 1,
            "failure_codes": failure_codes,
            "contract_errors": errors,
            "contract_warnings": warnings,
        },
        output_schema=original_packet.output_schema,
    )


def evaluate_agent_output(
    *,
    packet: PromptPacket,
    raw_output: str,
    attempt: int = 1,
    retry_policy: AgentRetryPolicy | None = None,
) -> AgentContractEvaluation:
    policy = retry_policy or AgentRetryPolicy()
    failure_codes: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    parsed_payload, parse_codes, parse_errors = _parse_json_object(raw_output)
    failure_codes.extend(parse_codes)
    errors.extend(parse_errors)

    validated_payload: dict[str, Any] | None = None
    if parsed_payload is not None:
        model_cls = CONTRACT_MODELS.get(packet.artifact)
        if model_cls is None:
            failure_codes.append("UNSUPPORTED_ARTIFACT_CONTRACT")
            errors.append(f"No agent contract model registered for artifact {packet.artifact}.")
        else:
            try:
                validated = model_cls.model_validate(parsed_payload)
                validated_payload = validated.model_dump(mode="json")
            except ValidationError as exc:
                failure_codes.append("SCHEMA_VALIDATION_FAILED")
                for error in exc.errors():
                    field_path = ".".join(str(segment) for segment in error.get("loc", ()))
                    message = error.get("msg", "invalid field")
                    errors.append(f"{field_path}: {message}" if field_path else message)

        context_errors = _check_context_ids(packet, parsed_payload)
        if context_errors:
            failure_codes.append("CONTEXT_ID_MISMATCH")
            errors.extend(context_errors)
        warnings.extend(_audit_warnings(packet, parsed_payload))

    failure_codes = list(dict.fromkeys(failure_codes))
    passed = not failure_codes and not errors
    retry_recommended = policy.should_retry(attempt=attempt, failure_codes=failure_codes)
    retry_packet = None
    if retry_recommended:
        retry_packet = build_retry_packet(
            original_packet=packet,
            failure_codes=failure_codes,
            errors=errors,
            warnings=warnings,
            attempt=attempt,
        )

    return AgentContractEvaluation(
        packet_id=packet.packet_id,
        artifact=packet.artifact,
        attempt=attempt,
        passed=passed,
        failure_codes=failure_codes,
        errors=errors,
        warnings=warnings,
        parsed_payload=parsed_payload,
        validated_payload=validated_payload,
        retry_recommended=retry_recommended,
        retry_packet=retry_packet,
    )
