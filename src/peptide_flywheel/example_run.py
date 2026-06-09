from peptide_flywheel.models import PeptideCandidate, PeptideModality, CandidateStatus
from peptide_flywheel.scoring import heuristic_manufacturability_score
from peptide_flywheel.reporting import candidate_card_markdown


def main() -> None:
    candidate = PeptideCandidate(
        candidate_id="CAND-001",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        target_id="TARGET-001",
        hypothesis_id="HYP-001",
        modality=PeptideModality.LINEAR,
        design_rationale="Example candidate used to test the scaffold.",
        status=CandidateStatus.DRAFT,
    )

    score = heuristic_manufacturability_score(candidate.sequence, candidate.modality.value)
    candidate.manufacturability_score = score.overall_score
    candidate.risk_flags = score.risk_flags
    candidate.predicted_properties = score.dimension_scores

    print(candidate_card_markdown(candidate))


if __name__ == "__main__":
    main()
