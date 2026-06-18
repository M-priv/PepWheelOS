# Red-Team Review

Candidate ID: AMP_SRC_DBAASP_1001
Result ID: 
Failure mode: Manufacturability/utility mismatch (not a failed assay result yet)

## What failed?

No assay failure is confirmed yet, but preflight and scoring indicate operational risk from sequence characteristics and manufacturing complexity likely at scale.

## Evidence

- High sequence length risk and elevated hydrophobicity risk in scoring
- Deamidation liability in amidated linear scaffold context
- No direct in-lab evidence yet to contradict these flags

## Most likely cause

Conservative selection bias for high activity profiles may be carrying non-ideal developability traits early.

## Alternative explanations

- The source literature assay context may overstate practical robustness.
- Some liabilities can be reduced with formulation or sequence truncation.

## Was this predicted?

Partly: manufacturability scoring correctly flagged this pattern before synthesis.

## How should the design change?

- Reduce contiguous hydrophobic stretches while preserving cationic termini.
- Consider N-terminal cap variants to improve synthetic robustness.

## How should the model or heuristic change?

- Increase penalty for long hydrophobic windows in broader family-level context, not only absolute length.

## What should be tested next?

- Request one truncated analog with reduced tail burden.
- Generate solubility and yield notes from CRO prior to scale expansion.
