from __future__ import annotations

from typing import Iterable
from .models import PeptideCandidate


def candidate_card_markdown(candidate: PeptideCandidate) -> str:
    lines = [
        f"# Candidate Card: {candidate.candidate_id}",
        "",
        f"Sequence: `{candidate.sequence}`",
        f"Target ID: `{candidate.target_id}`",
        f"Hypothesis ID: `{candidate.hypothesis_id}`",
        f"Modality: `{candidate.modality}`",
        f"Status: `{candidate.status}`",
        "",
        "## Design rationale",
        candidate.design_rationale or "To be populated.",
        "",
        "## Modifications",
        "\n".join(f"- {m}" for m in candidate.modifications) or "None recorded.",
        "",
        "## Predicted properties",
        "\n".join(f"- {k}: {v}" for k, v in candidate.predicted_properties.items()) or "Not yet populated.",
        "",
        "## Manufacturability",
        f"Score: {candidate.manufacturability_score if candidate.manufacturability_score is not None else 'Not scored'}",
        "",
        "## Risk flags",
        "\n".join(f"- {flag}" for flag in candidate.risk_flags) or "No flags recorded.",
    ]
    return "\n".join(lines)


def batch_summary_markdown(candidates: Iterable[PeptideCandidate]) -> str:
    lines = ["# Candidate Batch Summary", ""]
    for candidate in candidates:
        lines.append(
            f"- {candidate.candidate_id}: score={candidate.manufacturability_score}, "
            f"status={candidate.status}, flags={', '.join(candidate.risk_flags) or 'none'}"
        )
    return "\n".join(lines)
