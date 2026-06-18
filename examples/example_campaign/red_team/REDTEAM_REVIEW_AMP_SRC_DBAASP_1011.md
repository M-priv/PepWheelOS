# Red-Team Review

Candidate ID: AMP_SRC_DBAASP_1011
Result ID: 
Failure mode: Translational toxicity uncertainty

## What failed?

Public source data suggests useful antimicrobial potency but dose-dependent hemolysis signals.

## Evidence

- Candidate card lists dose-dependent hemolysis at higher concentrations.
- Short sequence with moderate aromatic load raises concentration-dependent membrane effects.

## Most likely cause

Narrow therapeutic window driven by physicochemical profile and hydrophobic-aromatic balance.

## Alternative explanations

- Potency and safety may be improved by formulation or exposure-time control.
- Dose-response in targeted assay panel may differ substantially from source conditions.

## Was this predicted?

Partly: model score is strong but safety nuance remains under-penalized.

## How should the design change?

- Keep only as a controlled follow-up candidate.
- Pair with at least one lower-aromatic analog before allocation.

## How should the model or heuristic change?

- Include an explicit haemolysis-risk proxy in candidate pre-selection, not only manufacturability score.

## What should be tested next?

- CRO request plus conservative dose range selection focused on separation of antibacterial versus hemolytic window.
