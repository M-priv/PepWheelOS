# Red-Team Review

Candidate ID: AMP_SRC_DBAASP_1004
Result ID: 
Failure mode: Safety margin concern

## What failed?

The candidate has known high hemolysis and membrane-disruption liability versus reported potency.

## Evidence

- Candidate card and public notes report high hemolysis above 5 µg/mL.
- High baseline manufacturability concern despite good bacterial activity context.
- Toxicity context suggests narrow translational margin.

## Most likely cause

Potency is likely driven by strong non-selective membrane activity.

## Alternative explanations

- Potency and toxicity could diverge if assay media and formulation differ from source conditions.
- Activity may be recoverable via protected/modified variants.

## Was this predicted?

No: current scoring captures some manufacturability signals but does not directly score this exact safety tradeoff.

## How should the design change?

- De-prioritize for near-term translation.
- Keep as a negative-control-like comparator for toxicity-aware optimization.

## How should the model or heuristic change?

- Add explicit toxicity-risk proxy where hemolysis/lipid-disruptive sequence motifs are weighted.

## What should be tested next?

- Run limited dose-ranging only if a safer variant is proposed.
- Prefer a safer scaffold for first-round CRO allocation.
