from pathlib import Path

import json

from peptide_flywheel.models import CandidateStatus, ExperimentalResult, PeptideCandidate, PeptideModality
from peptide_flywheel.dag import ResearchDAG
from peptide_flywheel.result_review import apply_results_to_candidates


def _candidate() -> PeptideCandidate:
    return PeptideCandidate(
        candidate_id="AMP_SRC_DBAASP_1001",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        target_id="TARGET-AMP-EX-01",
        hypothesis_id="HYP-AMP-EX-01",
        modality=PeptideModality.LINEAR,
        status=CandidateStatus.SCORED,
    )


def _result_pass() -> ExperimentalResult:
    return ExperimentalResult(
        result_id="RESULT-SIM-1001",
        candidate_id="AMP_SRC_DBAASP_1001",
        result_type="Simulated assay result",
        summary="Clear activity with low noise.",
        interpretation="Consistent reproducible signal.",
    )


def _result_fail() -> ExperimentalResult:
    return ExperimentalResult(
        result_id="RESULT-SIM-0690",
        candidate_id="AMP_SRC_DBAASP_0690",
        result_type="Simulated assay result",
        summary="No binding was confirmed.",
        interpretation="Interpretation was weak and noisy.",
        failure_modes=["NO_BINDING"],
    )


def test_apply_results_to_candidates_advances_and_rejects(tmp_path: Path) -> None:
    candidate_pass = _candidate()
    candidate_fail = _candidate().model_copy(update={"candidate_id": "AMP_SRC_DBAASP_0690"})
    success = apply_results_to_candidates(
        candidates=[candidate_pass, candidate_fail],
        results=[_result_pass(), _result_fail()],
        campaign_id="CAMP-TEST",
        run_id="RUN-001",
        output_dir=tmp_path / "review",
        strict=True,
    )

    reviewed_by_id = {candidate.candidate_id: candidate for candidate in success.candidates}
    assert reviewed_by_id["AMP_SRC_DBAASP_1001"].status == CandidateStatus.ADVANCED
    assert reviewed_by_id["AMP_SRC_DBAASP_0690"].status == CandidateStatus.REJECTED
    assert (tmp_path / "review" / "result_review_report.md").exists()
    assert (tmp_path / "review" / "closed_loop_recommendations.json").exists()
    assert (tmp_path / "review" / "next_round_plan.json").exists()
    assert (tmp_path / "review" / "campaign_decision.json").exists()
    assert (tmp_path / "review" / "campaign_recommendation_plan.json").exists()
    assert (tmp_path / "review" / "research_graph_result_review.json").exists()
    assert (tmp_path / "review" / "records" / "CAMP-TEST-RUN-001-AMP_SRC_DBAASP_1001-decision.json").exists()
    assert success.decisions
    assert success.recommendations
    assert success.campaign_recommendation_plan["campaign_id"] == "CAMP-TEST"
    assert success.campaign_decision.decision in {"proceed_to_next_round", "rework_pool", "pause"}
    assert success.next_round_plan["campaign_id"] == "CAMP-TEST"
    assert {d.campaign_id for d in success.decisions} == {"CAMP-TEST"}


def test_apply_results_to_candidates_merges_with_existing_dag(tmp_path: Path) -> None:
    base_dag = ResearchDAG()
    base_dag.add_node(
        "HYP-AMP-EX-01",
        "hypothesis",
        {"hypothesis_id": "HYP-AMP-EX-01", "target_id": "TARGET-AMP-EX-01", "claim": "Baseline"},
    )

    base_candidate = _candidate()
    base_dag.add_node(
        base_candidate.candidate_id,
        "peptide_candidate",
        {
            "candidate_id": base_candidate.candidate_id,
            "sequence": base_candidate.sequence,
            "target_id": base_candidate.target_id,
            "hypothesis_id": base_candidate.hypothesis_id,
            "status": base_candidate.status.value,
        },
    )
    base_dag.add_edge("HYP-AMP-EX-01", base_candidate.candidate_id, "supports")

    loaded = ResearchDAG.from_dict(base_dag.to_dict())

    success = apply_results_to_candidates(
        candidates=[base_candidate],
        results=[_result_pass()],
        campaign_id="CAMP-TEST",
        run_id="RUN-BASE",
        output_dir=tmp_path / "review-merge",
        dag=loaded,
        strict=True,
    )

    nodes = {node["id"] for node in success.dag.to_dict()["nodes"]}
    edges = {(edge["source"], edge["target"]) for edge in success.dag.to_dict()["edges"]}

    assert "HYP-AMP-EX-01" in nodes
    assert base_candidate.candidate_id in nodes
    assert "RESULT-SIM-1001" in nodes
    assert "CAMP-TEST-RUN-BASE-AMP_SRC_DBAASP_1001-decision" in nodes
    assert ("HYP-AMP-EX-01", base_candidate.candidate_id) in edges
    assert success.candidates[0].status == CandidateStatus.ADVANCED

    recommendations_path = tmp_path / "review-merge" / "closed_loop_recommendations.json"
    payload = json.loads(recommendations_path.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["recommendations"][0]["candidate_id"] == base_candidate.candidate_id

    nodes = {node["id"] for node in success.dag.to_dict()["nodes"]}
    assert f"CAMP-TEST-RUN-BASE-campaign-recommendation-plan" in nodes
    assert f"CAMP-TEST-RUN-BASE-next-round-plan" in nodes
    assert f"CAMP-TEST-RUN-BASE-campaign-decision" in nodes

    next_round_path = tmp_path / "review-merge" / "next_round_plan.json"
    campaign_decision_path = tmp_path / "review-merge" / "campaign_decision.json"
    assert next_round_path.exists()
    assert campaign_decision_path.exists()
    next_round_payload = json.loads(next_round_path.read_text(encoding="utf-8"))
    assert next_round_payload["campaign_id"] == "CAMP-TEST"
    campaign_decision_payload = json.loads(campaign_decision_path.read_text(encoding="utf-8"))
    assert campaign_decision_payload["decision_id"] == "CAMP-TEST-RUN-BASE-campaign-close-loop-decision"
