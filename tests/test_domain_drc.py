from __future__ import annotations

import pytest

from peptide_flywheel.contracts import (
    Contract,
    ContractSeverity,
    ContractViolation,
    assume_context_has_keys,
    assume_valid_sequence,
    enforce_contract,
    guarantee_bounded_score,
    guarantee_non_null_output,
)
from peptide_flywheel.domain_drc import (
    DRCSeverity,
    calculate_gravy,
    calculate_net_charge,
    check_aspartimide_motifs,
    check_cysteine_pairing,
    check_hydrophobic_runs,
    check_isoelectric_precipitation,
    check_steric_hindrance,
    run_biological_drc_suite,
)


# --- Tests for contracts.py ---

def test_assume_valid_sequence_pass():
    contract = Contract(
        name="CandidateScoringContract",
        assumptions=[assume_valid_sequence("sequence", min_len=4, max_len=30)],
        guarantees=[guarantee_non_null_output(), guarantee_bounded_score("score", 0.0, 100.0)],
    )

    @enforce_contract(contract)
    def dummy_score(sequence: str) -> dict:
        return {"sequence": sequence, "score": 85.0}

    result = dummy_score(sequence="KWKLFKKIE")
    assert result["score"] == 85.0


def test_assume_valid_sequence_non_standard_residues():
    contract = Contract(
        name="CandidateScoringContract",
        assumptions=[assume_valid_sequence("sequence")],
    )

    @enforce_contract(contract)
    def dummy_score(sequence: str) -> dict:
        return {"sequence": sequence}

    with pytest.raises(ContractViolation) as exc_info:
        dummy_score(sequence="KWKLFKZX")
    assert "non-standard amino acid" in str(exc_info.value)
    assert exc_info.value.severity == ContractSeverity.FATAL


def test_assume_context_has_keys_missing():
    contract = Contract(
        name="ContextCheckContract",
        assumptions=[assume_context_has_keys("target_id", "hypothesis_id")],
    )

    @enforce_contract(contract)
    def dummy_runner(target_id: str, hypothesis_id: str | None = None) -> bool:
        return True

    with pytest.raises(ContractViolation) as exc_info:
        dummy_runner(target_id="TARG-001", hypothesis_id=None)
    assert "missing required parameters" in str(exc_info.value)


def test_guarantee_bounded_score_violation():
    contract = Contract(
        name="ScoreBoundsContract",
        guarantees=[guarantee_bounded_score("score", min_val=0.0, max_val=100.0)],
    )

    @enforce_contract(contract)
    def bad_score() -> dict:
        return {"score": 150.0}  # Exceeds max_val

    with pytest.raises(ContractViolation) as exc_info:
        bad_score()
    assert "outside guaranteed bounds" in str(exc_info.value)


# --- Tests for domain_drc.py ---

def test_check_aspartimide_motifs_detected():
    violations = check_aspartimide_motifs("KWKLDGSFK")
    assert len(violations) == 1
    assert violations[0].rule_id == "DRC-001"
    assert violations[0].culprit_motif == "DG"
    assert violations[0].positions == [5, 6]
    assert violations[0].severity == DRCSeverity.FATAL
    assert violations[0].failure_code == "SYN_MODIFICATION_FAILED"


def test_check_hydrophobic_runs_detected():
    violations = check_hydrophobic_runs("ACDEFVVVVVGHIKL", max_consecutive=5)
    assert len(violations) == 1
    assert violations[0].rule_id == "DRC-002"
    assert violations[0].culprit_motif == "FVVVVV"
    assert violations[0].positions == [5, 6, 7, 8, 9, 10]
    assert violations[0].severity == DRCSeverity.FATAL
    assert violations[0].failure_code == "SYN_HYDROPHOBIC_SEQUENCE"



def test_check_isoelectric_precipitation():
    # Sequence with neutral net charge and high GRAVY
    neutral_hydrophobic = "ILVFAAGFAVLI"
    violations = check_isoelectric_precipitation(neutral_hydrophobic)
    assert len(violations) >= 1
    assert any(v.failure_code == "LOW_AQUEOUS_SOLUBILITY" for v in violations)


def test_check_cysteine_pairing():
    # Odd cysteine count
    violations = check_cysteine_pairing("CKWLFKKIECKWLFLG")  # 2 Cys -> should pass
    assert len(violations) == 0

    odd_violations = check_cysteine_pairing("CKWLFKKIEKWLFLG")  # 1 Cys -> should flag
    assert len(odd_violations) == 1
    assert odd_violations[0].failure_code == "OXIDATION_LIABILITY"


def test_check_steric_hindrance():
    violations = check_steric_hindrance("AKWPPPPKIE")
    assert len(violations) == 1
    assert violations[0].rule_id == "DRC-005"
    assert violations[0].culprit_motif == "PPPP"


def test_run_biological_drc_suite_clean_pass():
    clean_amp = "KWKLFKKIEKWLFLG"
    summary = run_biological_drc_suite(clean_amp)
    assert summary.passed_hard_drc is True
    assert len(summary.hard_stop_reasons) == 0
    assert summary.net_charge_ph74 > 3.0  # Positively charged AMP


def test_run_biological_drc_suite_with_hard_stops():
    flawed_peptide = "KWKLDGVVVVVGHC"
    summary = run_biological_drc_suite(flawed_peptide)
    assert summary.passed_hard_drc is False
    assert len(summary.hard_stop_reasons) >= 2  # Aspartimide and Poly-hydrophobic
    assert len(summary.suggested_remediations) >= 2
    assert "Replace Gly/Ser with Ala" in summary.suggested_remediations[0] or "pseudoproline" in summary.suggested_remediations[0]

    d_dict = summary.to_dict()
    assert d_dict["passed_hard_drc"] is False
    assert d_dict["violation_count"] >= 3
