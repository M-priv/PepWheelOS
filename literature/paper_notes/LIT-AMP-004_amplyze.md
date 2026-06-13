# AmpLyze: A Deep Learning Model for Predicting the Hemolytic Concentration

## Metadata

Title: AmpLyze: A Deep Learning Model for Predicting the Hemolytic Concentration
Authors: Peng Qiu; Hanqi Feng; Meng-Chun Zhang; Barnabas Poczos
Year: 2025
arXiv ID: 2507.08162
URL: https://arxiv.org/abs/2507.08162
Module tags: module_4,module_6,module_8
Priority: must_read_now

## Summary

AmpLyze targets HC50 prediction as a direct quantitative toxicity readout and incorporates attention-style architecture and residue-level interpretation, making toxicity screening more actionable than binary hemolysis classification alone.

## Why this matters for the peptide flywheel

It upgrades safety scoring from binary labels to concentration-aware risk modeling and supports manufacturability-aware rejection with confidence estimates.

## Dataset used

Abstract-level says curated peptide toxicity datasets; full text needed for source repositories and preprocessing details.

## Method/model

Transformer-like deep model with combined local/global residue/context encoders.

## Validation design

Regression metrics on held-out peptide cohorts with model explanation analyses.

## Leakage or bias risks

Cross-dataset contamination risk without explicit homology-aware split disclosure; verify splits if used in production.

## Toxicity/haemolysis relevance

Primary relevance: direct hemolysis concentration prediction.

## Manufacturability relevance

Moderate: concentration-based toxicity can be fused with cost/sequence complexity filters.

## Agentic workflow relevance

Useful as a callable scoring node in the design-to-test stage.

## Limitations

Assay harmonization and dataset provenance are not fully explicit in abstract snippet.

## What to implement

- Add HC50 model candidate with uncertainty-aware gating.
- Calibrate thresholds against internal toxicity ladder (e.g., acceptable HC50).

## What to avoid

- Avoid treating model confidence as safety proof without external assay context.

## Questions I should manually review

- Are HC50 values normalized across salt/media conditions?
- Exact split policy and leakage guards in full paper.
