import pytest

from peptide_flywheel.models import CandidateStatus, Hypothesis, PeptideCandidate, Target
from peptide_flywheel.workflows import run_manual_flywheel_round


def _base_objects():
    target = Target(
        target_id="TARGET-001",
        name="Example Target",
        use_case="Proof of concept",
        rationale="Smoke test target.",
    )
    hypothesis = Hypothesis(
        hypothesis_id="HYP-001",
        target_id="TARGET-001",
        claim="Validate workflow plumbing.",
    )
    return target, hypothesis


def test_manual_flywheel_round_builds_artifacts(tmp_path):
    target, hypothesis = _base_objects()
    candidate = PeptideCandidate(
        candidate_id="CAND-001",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
    )

    result = run_manual_flywheel_round(
        target=target,
        hypothesis=hypothesis,
        candidates=[candidate],
        run_id="RUN-001",
        campaign_id="CAMP-001",
        output_dir=tmp_path / "manual_round",
    )

    assert result.dag.validate_acyclic()
    assert len(result.candidates) == 1
    assert result.candidates[0].status == CandidateStatus.SCORED
    assert result.summary_markdown.startswith("# Candidate Batch Summary")
    assert result.validation_errors == []
    assert result.validation_warnings == []

    assert (tmp_path / "manual_round" / "records" / "CAND-001.json").exists()
    assert (tmp_path / "manual_round" / "research_graph.json").exists()
    assert (tmp_path / "manual_round" / "round_report.md").exists()


def test_manual_flywheel_round_strict_mode_rejects_invalid_sequence(tmp_path):
    target, hypothesis = _base_objects()
    bad_candidate = PeptideCandidate(
        candidate_id="CAND-002",
        sequence="ACZZZ",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
    )

    with pytest.raises(ValueError, match="unsupported residues"):
        run_manual_flywheel_round(
            target=target,
            hypothesis=hypothesis,
            candidates=[bad_candidate],
            run_id="RUN-002",
            campaign_id="CAMP-001",
            output_dir=tmp_path / "manual_round_invalid",
            strict=True,
        )


def test_manual_flywheel_round_lenient_mode_reports_invalid_candidates(tmp_path):
    target, hypothesis = _base_objects()
    bad_candidate = PeptideCandidate(
        candidate_id="CAND-002",
        sequence="ACZZZ",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
    )
    good_candidate = PeptideCandidate(
        candidate_id="CAND-003",
        sequence="KLMNPQRSTVWY",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
    )

    result = run_manual_flywheel_round(
        target=target,
        hypothesis=hypothesis,
        candidates=[bad_candidate, good_candidate],
        run_id="RUN-003",
        campaign_id="CAMP-001",
        output_dir=tmp_path / "manual_round_lenient",
        strict=False,
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].candidate_id == "CAND-003"
    assert len(result.validation_errors) == 1
    assert result.validation_warnings == []
