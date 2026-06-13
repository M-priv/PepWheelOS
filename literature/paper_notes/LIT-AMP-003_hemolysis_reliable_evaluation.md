# Prediction of Hemolysis Tendency of Peptides using a Reliable Evaluation Method

## Metadata

Title: Prediction of Hemolysis Tendency of Peptides using a Reliable Evaluation Method
Authors: Ali Raza; Hafiz Saud Arshad
Year: 2020
arXiv ID: 2012.06470
URL: https://arxiv.org/abs/2012.06470
Module tags: module_2,module_3,module_4
Priority: useful_now

## Summary

The paper proposes a reliability-oriented evaluation protocol for peptide hemolysis prediction using similarity-aware splits and robust performance checks to reduce overestimation from homologous leakage.

## Why this matters for the peptide flywheel

Directly informs the haemolysis gate and leakage-aware validation policy for AMP safety filtering.

## Dataset used

Hemo-peptide datasets built from public peptide repositories (details need full-text confirmation for exact counts).

## Method/model

Binary/continuous hemolysis predictor with explicit train-test filtering constraints.

## Validation design

Homology-aware split strategy (<40% similarity threshold mentioned), plus reported reliability comparisons.

## Leakage or bias risks

Potential outdated feature engineering and assay harmonization assumptions; still useful as a control strategy template.

## Toxicity/haemolysis relevance

Core paper for haemolysis modeling assumptions and thresholding.

## Manufacturability relevance

Low direct relevance.

## Agentic workflow relevance

Moderate; can be encoded as a hard constraint in red-team and fail-safe agents.

## Limitations

Older baseline and feature assumptions; should be revalidated on modern sequence embeddings.

## What to implement

- Add strict sequence-similarity blocking for hemolysis validation folds.
- Log similarity thresholds used in each evaluation run.

## What to avoid

- Do not apply its exact model architecture unchanged; only its leakage policy is high-confidence reusable.

## Questions I should manually review

- Exact dataset version and feature preprocessing steps.
- Whether the 40% threshold is residue-level or alignment-level in their scripts.
