from pathlib import Path
from peptide_flywheel.models import PeptideCandidate
from peptide_flywheel.reporting import candidate_card_markdown

candidate = PeptideCandidate(
    candidate_id="CAND-NEW",
    sequence="POPULATE",
    target_id="TARGET-NEW",
    hypothesis_id="HYP-NEW",
    design_rationale="Populate design rationale.",
)

output = Path("data/results/CAND-NEW.md")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(candidate_card_markdown(candidate), encoding="utf-8")
print(f"Wrote {output}")
