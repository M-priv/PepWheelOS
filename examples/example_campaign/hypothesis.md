# Hypothesis Record

Hypothesis ID: HYP-AMP-EX-01
Target ID: TARGET-AMP-EX-01
Campaign ID: CAMP-AMP-EX-01

## Claim

An antimicrobial discovery campaign seeded from curated public AMPs can rapidly converge on a shortlist with acceptable manufacturability risk using a transparent workflow that includes data governance checks and structured candidate documentation.

## Mechanistic rationale

Peptides in this dossier include cationic amphipathic and β-hairpin-like motifs with prior membrane-interaction evidence; these motifs provide a known starting manifold for antibacterial activity, allowing early filtering by sequence-level liabilities.

## Design strategy

- Reuse the existing seed set to avoid overfitting to a single motif family.
- Prioritise diversity across linear/cyclic, high/low charge, and size range.
- Apply manufacturability scoring before moving any candidate into simulated assay planning.

## Success criteria

- At least 10 candidate cards are fully documented and traceable.
- Every manual batch has at least one data-governance preflight report.
- Candidate shortlist includes explicit risk flags and next actions.

## Rejection criteria

- Candidates with unresolved sequence-level integrity failures.
- Candidates with unresolved split-leakage violations in governance checks.
- Candidates failing minimum manufacturability score threshold without strong rationale.

## Assumptions

- The seed cards are used for workflow validation, not clinical claims.
- Source labels and assay units are sufficiently comparable for first-pass triage.

## Uncertainties

- Relative assay conditions and units are not fully harmonized across sources.
- Holdout validation splits are not yet embedded in all source CSV rows.

## Required evidence

- Candidate card markdown for each shortlisted peptide.
- Manual round report and governance events for each run.
- Future: simulated or real assay result records with failure-mode mapping.
