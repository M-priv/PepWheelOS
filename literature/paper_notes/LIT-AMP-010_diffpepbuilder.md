# Target-Specific De Novo Peptide Binder Design with DiffPepBuilder

## Metadata

Title: Target-Specific De Novo Peptide Binder Design with DiffPepBuilder
Authors: Fanhao Wang; Yuzhe Wang; Laiyi Feng; Changsheng Zhang; Luhua Lai
Year: 2024
arXiv ID: 2405.00128
URL: https://arxiv.org/abs/2405.00128
Module tags: module_9,module_7,module_1
Priority: useful_next

## Summary

DiffPepBuilder generates peptide binders conditioned on target structures using geometry-aware diffusion and a synthetic structure-paired dataset for direct binder design, including disulfide patterns and complex stability cues.

## Why this matters for the peptide flywheel

Useful for the binder branch and for defining realistic synthesis-aware binder candidates before synthesis.

## Dataset used

PepPC-F (synthetic complex-based dataset) and target structure inputs.

## Method/model

SE(3)-equivariant/binder-focused diffusion with target conditioning.

## Validation design

Binding-site recovery and downstream scoring across held-out targets; compare against baselines.

## Leakage or bias risks

Synthetic dataset generation and target overlap can bias gains; include target-identity blocking in validation.

## Toxicity/haemolysis relevance

Indirect.

## Manufacturability relevance

Targeted binder topology can affect synthesis complexity; include binder-loop constraints in manufacturability scoring.

## Agentic workflow relevance

High when orchestrating target-specific design tasks.

## Limitations

May underperform on small, noisy, or non-enzymatic targets.

## What to implement

- Add binder design tool path with explicit chain-length and disulfide constraints.
- Require post-generation cross-check against structural templates.

## What to avoid

- Do not use synthetic-only performance claims to approve therapeutic candidates.

## Questions I should manually review

- How are failed docking/structure checks handled in the loop?
- Are training targets homologous to your current pathogens’ proteins?
