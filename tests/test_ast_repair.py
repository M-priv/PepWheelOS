from __future__ import annotations

from peptide_flywheel.ast_repair import (
    deterministic_ast_normalization,
    repair_candidate_card_ast,
)


def test_deterministic_ast_normalization():
    raw_payload = {
        "candidate_id": "WRONG-ID",
        "sequence": "  kwklfkkie  ",
        "manufacturability_score": "0.85",
        "overall_score": -5.0,
        "risk_flags": "HYDROPHOBIC, OXIDATION",
    }
    expected_context = {
        "candidate_id": "CAND-001",
        "target_id": "TARG-001",
        "hypothesis_id": "HYP-001",
    }

    normalized, repairs = deterministic_ast_normalization(raw_payload, expected_context)

    # Context IDs aligned
    assert normalized["candidate_id"] == "CAND-001"
    assert normalized["target_id"] == "TARG-001"
    assert normalized["hypothesis_id"] == "HYP-001"

    # Sequence cleaned
    assert normalized["sequence"] == "KWKLFKKIE"

    # Scores coerced and clamped
    assert normalized["manufacturability_score"] == 0.85
    assert normalized["overall_score"] == 0.0  # Clamped from -5.0

    # Comma-separated string coerced to list
    assert normalized["risk_flags"] == ["HYDROPHOBIC", "OXIDATION"]

    assert len(repairs) >= 4


def test_repair_candidate_card_ast_master():
    raw = {"sequence": "acde", "manufacturability_score": "0.92"}
    ctx = {"candidate_id": "CAND-0042"}

    result = repair_candidate_card_ast(raw, expected_context=ctx)

    assert result.repaired_payload["candidate_id"] == "CAND-0042"
    assert result.repaired_payload["sequence"] == "ACDE"
    assert result.repaired_payload["manufacturability_score"] == 0.92
    assert result.requires_llm_micro_repair is False


def test_ast_repair_clamping_and_hallucination_warning():
    raw_payload = {
        "candidate_id": "CAND-001",
        "sequence": "KWK",
        "confidence": "85.0",           # 85% percentage -> should auto-normalise to 0.85
        "overall_score": 105.0,          # >100 -> should clamp ceiling to 100.0
        "affinity_score": -500.0,        # Extreme negative hallucination -> clamp to 0.0 & warn
    }

    normalized, repairs = deterministic_ast_normalization(raw_payload)

    # 1. Verify percentage auto-normalisation
    assert normalized["confidence"] == 0.85

    # 2. Verify ceiling clamping
    assert normalized["overall_score"] == 100.0

    # 3. Verify floor clamping
    assert normalized["affinity_score"] == 0.0

    # 4. Verify explicit hallucination warning was logged
    warning_logs = [r for r in repairs if "WARNING" in r and "Extreme out-of-bounds" in r]
    assert len(warning_logs) == 1
    assert "-500.0" in warning_logs[0]

