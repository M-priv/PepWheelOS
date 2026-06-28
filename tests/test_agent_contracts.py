import json

from peptide_flywheel.agent_contracts import evaluate_agent_output
from peptide_flywheel.models import Hypothesis, PeptideCandidate, Target, PeptideModality
from peptide_flywheel.prompt_pipeline import build_candidate_card_prompt


def _packet():
    target = Target(
        target_id="TARGET-001",
        name="Target",
        organism="human",
        use_case="benchmark",
        rationale="unit",
    )
    hypothesis = Hypothesis(
        hypothesis_id="HYP-001",
        target_id="TARGET-001",
        claim="Candidate should bind target with low toxicity.",
    )
    candidate = PeptideCandidate(
        candidate_id="CAND-001",
        sequence="ACDEFGHIKL",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
    )
    return build_candidate_card_prompt(
        candidate=candidate,
        target=target,
        hypothesis=hypothesis,
        campaign_id="CAMP-001",
        run_id="RUN-001",
    )


def test_evaluate_agent_output_accepts_valid_contract_output():
    packet = _packet()
    raw_output = json.dumps(
        {
            "candidate_id": "CAND-001",
            "sequence": "ACDEFGHIKL",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
            "design_rationale": "Short candidate for unit testing.",
            "manufacturability_score": 88.0,
            "risk_flags": ["LOW_TEST_RISK"],
        }
    )

    evaluation = evaluate_agent_output(packet=packet, raw_output=raw_output)

    assert evaluation.passed
    assert evaluation.validated_payload["candidate_id"] == "CAND-001"
    assert not evaluation.retry_recommended
    assert evaluation.retry_packet is None


def test_evaluate_agent_output_builds_retry_packet_for_schema_failure():
    packet = _packet()
    raw_output = json.dumps(
        {
            "candidate_id": "CAND-001",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
        }
    )

    evaluation = evaluate_agent_output(packet=packet, raw_output=raw_output, attempt=1)

    assert not evaluation.passed
    assert "SCHEMA_VALIDATION_FAILED" in evaluation.failure_codes
    assert evaluation.retry_recommended
    assert evaluation.retry_packet is not None
    assert evaluation.retry_packet.packet_id == f"{packet.packet_id}-retry-2"
    assert "sequence" in " ".join(evaluation.errors)


def test_evaluate_agent_output_catches_context_id_mismatch():
    packet = _packet()
    raw_output = json.dumps(
        {
            "candidate_id": "CAND-OTHER",
            "sequence": "ACDEFGHIKL",
            "target_id": "TARGET-001",
            "hypothesis_id": "HYP-001",
            "modality": "linear",
        }
    )

    evaluation = evaluate_agent_output(packet=packet, raw_output=raw_output)

    assert not evaluation.passed
    assert "CONTEXT_ID_MISMATCH" in evaluation.failure_codes
    assert evaluation.retry_recommended
