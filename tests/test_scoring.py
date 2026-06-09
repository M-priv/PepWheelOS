from peptide_flywheel.scoring import heuristic_manufacturability_score


def test_score_returns_valid_range():
    result = heuristic_manufacturability_score("ACDEFGHIKLMNPQRSTVWY")
    assert 0 <= result.overall_score <= 100
    assert isinstance(result.risk_flags, list)
