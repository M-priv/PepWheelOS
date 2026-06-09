from peptide_flywheel.models import PeptideCandidate


def test_candidate_model():
    candidate = PeptideCandidate(
        candidate_id="CAND-001",
        sequence="ACDE",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
    )
    assert candidate.sequence == "ACDE"
