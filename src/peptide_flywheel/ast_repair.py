import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError


@dataclass
class ASTRepairResult:
    repaired_payload: Dict[str, Any]
    deterministic_repairs_applied: List[str]
    isolated_invalid_fields: List[str]
    requires_llm_micro_repair: bool


def deterministic_ast_normalization(
    raw_payload: Dict[str, Any],
    expected_context: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Apply zero-LLM deterministic normalization to raw JSON payloads.
    
    Fixes:
    - Context ID injection / alignment
    - Sequence whitespace stripping & IUPAC uppercasing
    - Numeric string-to-float coercion
    - Score bounding / clamping
    - Empty list / dict defaults
    """
    payload = copy.deepcopy(raw_payload)
    repairs_applied: List[str] = []

    # 1. Inject or enforce expected context IDs
    if expected_context:
        for id_key in ("target_id", "hypothesis_id", "candidate_id", "campaign_id", "run_id"):
            expected_val = expected_context.get(id_key)
            if expected_val and payload.get(id_key) != expected_val:
                payload[id_key] = expected_val
                repairs_applied.append(f"Injected/aligned context field '{id_key}' = '{expected_val}'")

    # 2. Normalize sequence string
    if "sequence" in payload and isinstance(payload["sequence"], str):
        clean_seq = payload["sequence"].strip().upper()
        if clean_seq != payload["sequence"]:
            payload["sequence"] = clean_seq
            repairs_applied.append("Normalized sequence (stripped whitespace and uppercased)")

    # 3. Numeric string coercion and clamping for scores
    score_fields = (
        "manufacturability_score",
        "overall_score",
        "affinity_score",
        "liability_score",
        "confidence",
    )
    for field_name in score_fields:
        if field_name in payload and payload[field_name] is not None:
            val = payload[field_name]
            if isinstance(val, str):
                try:
                    val = float(val.strip())
                    payload[field_name] = val
                    repairs_applied.append(f"Coerced '{field_name}' from string '{payload[field_name]}' to float {val}")
                except ValueError:
                    pass

            # If score is a float, check bounds
            if isinstance(payload[field_name], (int, float)):
                orig_val = float(payload[field_name])
                
                # Flag extreme hallucinations (e.g. |score| > 150)
                if orig_val < -10.0 or orig_val > 150.0:
                    repairs_applied.append(f"WARNING: Extreme out-of-bounds value {orig_val} detected on '{field_name}' (potential hallucination)")

                # Clamp negative floor
                if orig_val < 0.0:
                    payload[field_name] = 0.0
                    repairs_applied.append(f"Clamped negative '{field_name}' {orig_val} to 0.0")
                elif field_name in ("confidence", "affinity_score") and 1.0 < orig_val <= 100.0:
                    # Normalise 0-100 percentage to 0.0-1.0 probability
                    payload[field_name] = orig_val / 100.0
                    repairs_applied.append(f"Normalised percentage '{field_name}' {orig_val} to {payload[field_name]}")
                elif orig_val > 100.0:
                    payload[field_name] = 100.0
                    repairs_applied.append(f"Clamped ceiling on '{field_name}' {orig_val} to 100.0")


    # 4. Normalize list fields
    list_fields = ("risk_flags", "evidence_required", "failure_hypotheses", "acceptance_criteria", "rejection_criteria", "controls")
    for lf in list_fields:
        if lf in payload:
            if isinstance(payload[lf], str):
                # If LLM passed comma-separated string instead of list
                items = [item.strip() for item in payload[lf].split(",") if item.strip()]
                payload[lf] = items
                repairs_applied.append(f"Coerced comma-delimited string '{lf}' into list of {len(items)} items")
            elif not isinstance(payload[lf], list):
                payload[lf] = []

    return payload, repairs_applied


def isolate_invalid_ast_subfields(validation_error: ValidationError) -> List[str]:
    """Extract path locators of invalid subfields from Pydantic ValidationError."""
    return list(dict.fromkeys(".".join(map(str, err.get("loc", ()))) for err in validation_error.errors() if err.get("loc")))



def repair_candidate_card_ast(
    raw_payload: Dict[str, Any],
    expected_context: Optional[Dict[str, Any]] = None,
    validation_error: Optional[ValidationError] = None,
) -> ASTRepairResult:
    """Master AST repair engine combining deterministic normalization and subtree error isolation."""
    normalized_payload, repairs = deterministic_ast_normalization(raw_payload, expected_context)
    
    invalid_fields: List[str] = []
    if validation_error:
        invalid_fields = isolate_invalid_ast_subfields(validation_error)

    return ASTRepairResult(
        repaired_payload=normalized_payload,
        deterministic_repairs_applied=repairs,
        isolated_invalid_fields=invalid_fields,
        requires_llm_micro_repair=len(invalid_fields) > 0,
    )
