from __future__ import annotations

import pytest

from peptide_flywheel.dialectic import (
    AdvocateAgentRunner,
    DialecticArbiter,
    DialecticDecision,
    ScepticAgentRunner,
)
from peptide_flywheel.models import Hypothesis, PeptideCandidate, PeptideModality, Target


@pytest.fixture
def sample_target() -> Target:
    return Target(
        target_id="TARG-AMP-001",
        name="Pseudomonas aeruginosa OM",
        use_case="Targeting bacterial outer membrane permeability",
        rationale="Disrupting lipopolysaccharide (LPS) barrier",
    )


@pytest.fixture
def sample_hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="HYP-001",
        target_id="TARG-AMP-001",
        claim="Cationic amphipathic alpha-helices selectively disrupt bacterial membranes.",
        design_strategy="linear",
    )


def test_dialectic_consensus_pass(sample_target: Target, sample_hypothesis: Hypothesis):
    candidate = PeptideCandidate(
        candidate_id="CAND-001",
        sequence="KWKLFKKIEKWLFLG",
        target_id="TARG-AMP-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
        design_rationale="Balanced cationic amphipathic peptide.",
    )

    advocate = AdvocateAgentRunner()
    sceptic = ScepticAgentRunner()
    arbiter = DialecticArbiter(dissensus_threshold=0.35)

    advocate_case = advocate.build_case(candidate, sample_target, sample_hypothesis, custom_affinity_score=0.88)
    sceptic_case = sceptic.falsify_candidate(candidate, sample_target, advocate_case, custom_liability_score=0.10)

    verdict = arbiter.adjudicate(candidate, sample_target, advocate_case, sceptic_case)

    assert verdict.decision == DialecticDecision.PASS
    assert verdict.hard_drc_passed is True
    assert verdict.dissensus_delta < 0.35
    assert len(verdict.falsification_tests) > 0


def test_dialectic_hard_drc_reject(sample_target: Target, sample_hypothesis: Hypothesis):
    candidate = PeptideCandidate(
        candidate_id="CAND-002",
        sequence="KWKLDGVVVVVGHC",  # Has DG aspartimide + VVVVV beta sheet run
        target_id="TARG-AMP-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
    )

    advocate = AdvocateAgentRunner()
    sceptic = ScepticAgentRunner()
    arbiter = DialecticArbiter()

    advocate_case = advocate.build_case(candidate, sample_target, sample_hypothesis, custom_affinity_score=0.90)
    sceptic_case = sceptic.falsify_candidate(candidate, sample_target, advocate_case)

    verdict = arbiter.adjudicate(candidate, sample_target, advocate_case, sceptic_case)

    assert verdict.decision == DialecticDecision.REJECT
    assert verdict.hard_drc_passed is False
    assert any("Hard Biological DRC Invariant" in r for r in verdict.reasons)


def test_dialectic_high_dissensus_routes_to_discriminative_assay(sample_target: Target, sample_hypothesis: Hypothesis):
    candidate = PeptideCandidate(
        candidate_id="CAND-003",
        sequence="KWKLFKKIEKWLFLG",
        target_id="TARG-AMP-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
    )

    advocate = AdvocateAgentRunner()
    sceptic = ScepticAgentRunner()
    arbiter = DialecticArbiter(dissensus_threshold=0.35)

    # Advocate claims very high affinity (0.95), but Sceptic finds significant liability (0.60)
    # dissensus_delta = |0.95 - (1.0 - 0.60)| = |0.95 - 0.40| = 0.55 > 0.35
    advocate_case = advocate.build_case(candidate, sample_target, sample_hypothesis, custom_affinity_score=0.95)
    sceptic_case = sceptic.falsify_candidate(candidate, sample_target, advocate_case, custom_liability_score=0.60)

    verdict = arbiter.adjudicate(candidate, sample_target, advocate_case, sceptic_case)

    assert verdict.decision == DialecticDecision.DISCRIMINATIVE_ASSAY
    assert verdict.dissensus_delta == pytest.approx(0.55, 0.01)
    assert any("High epistemic dissensus" in r for r in verdict.reasons)

    v_dict = verdict.to_dict()
    assert v_dict["decision"] == "DISCRIMINATIVE_ASSAY"
    assert v_dict["dissensus_delta"] == 0.55
