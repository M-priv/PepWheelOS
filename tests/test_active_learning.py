import json
from pathlib import Path

import pytest

from peptide_flywheel.active_learning import run_active_learning_simulation
from peptide_flywheel.models import PeptideCandidate, PeptideModality


def _candidate(candidate_id: str, sequence: str) -> PeptideCandidate:
    return PeptideCandidate(
        candidate_id=candidate_id,
        sequence=sequence,
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
    )


def test_active_learning_simulation_writes_plan_prompt_and_graph(tmp_path: Path) -> None:
    candidates = [
        _candidate("CAND-001", "ACDEFGHIKLMNPQRSTVWY"),
        _candidate("CAND-002", "KKLLKKLLKKLL"),
        _candidate("CAND-003", "GGGGSSSSNNNN"),
    ]

    result = run_active_learning_simulation(
        candidates=candidates,
        campaign_id="CAMP-TEST",
        run_id="RUN-AL-001",
        output_dir=tmp_path / "active_learning",
        batch_size=2,
    )

    assert len(result.rankings) == 3
    assert len(result.selected_candidate_ids) == 2
    assert result.dag.validate_acyclic()
    assert result.prompt_packet.artifact == "active_learning_scoring_summary"
    assert result.summary_markdown.startswith("# Active-Learning Simulation")

    assert (tmp_path / "active_learning" / "active_learning_plan.json").exists()
    assert (tmp_path / "active_learning" / "active_learning_rankings.json").exists()
    assert (tmp_path / "active_learning" / "active_learning_scoring_summary_prompt.json").exists()
    assert (tmp_path / "active_learning" / "research_graph_active_learning.json").exists()
    assert (tmp_path / "active_learning" / "active_learning_report.md").exists()

    plan = json.loads((tmp_path / "active_learning" / "active_learning_plan.json").read_text(encoding="utf-8"))
    assert plan["campaign_id"] == "CAMP-TEST"
    assert plan["selection_policy"]["batch_size"] == 2
    assert plan["selected_candidate_ids"] == result.selected_candidate_ids


def test_active_learning_simulation_rejects_empty_candidate_pool(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="At least one candidate"):
        run_active_learning_simulation(
            candidates=[],
            campaign_id="CAMP-TEST",
            run_id="RUN-EMPTY",
            output_dir=tmp_path / "active_learning",
        )
