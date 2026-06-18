from peptide_flywheel.models import Hypothesis, PeptideCandidate, Target, PeptideModality
from peptide_flywheel.prompt_pipeline import build_prompt_batch, prompt_manifest


def _target() -> Target:
    return Target(
        target_id="TARGET-001",
        name="Target",
        organism="human",
        use_case="benchmark",
        rationale="unit",
    )


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="HYP-001",
        target_id="TARGET-001",
        claim="Candidate should bind target with low toxicity.",
        rejection_criteria=["toxicity"],
    )


def _candidate(cid: str) -> PeptideCandidate:
    return PeptideCandidate(
        candidate_id=cid,
        sequence="ACDEFGHIKL",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
    )


def test_build_prompt_batch_includes_all_artifact_types():
    packets = build_prompt_batch(
        target=_target(),
        hypothesis=_hypothesis(),
        candidates=[_candidate("CAND-001"), _candidate("CAND-002")],
        campaign_id="CAMP-001",
        run_id="RUN-001",
    )
    assert len(packets) == 7  # one target dossier + 3 per candidate
    artifacts = sorted({packet.artifact for packet in packets})
    assert "target_dossier" in artifacts
    assert "candidate_card" in artifacts
    assert "red_team_review" in artifacts
    assert "assay_pack" in artifacts

    manifest = prompt_manifest(packets)
    assert manifest["packet_count"] == 7
    assert len(manifest["agents"]) == 4

