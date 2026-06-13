# Full-Atom Peptide Design with Geometric Latent Diffusion

## Metadata

Title: Full-Atom Peptide Design with Geometric Latent Diffusion
Authors: Xiangzhe Kong; Yinjun Jia; Wenbing Huang; Yang Liu
Year: 2024
arXiv ID: 2402.13555
URL: https://arxiv.org/abs/2402.13555
Module tags: module_9,module_5,module_6
Priority: useful_next

## Summary

This paper introduces full-atom latent diffusion for peptide generation with geometric constraints, pushing beyond sequence-only methods toward physically coherent structure-generation for binder tasks.

## Why this matters for the peptide flywheel

Useful for adding a structure-aware manufacturability/sanity check before peptide synthesis planning.

## Dataset used

Likely structure-conditioned peptide datasets (PDB-derived); full details need full-text check.

## Method/model

Latent diffusion on atom-level geometry with shared transform operations.

## Validation design

Structure recovery and binding compatibility tests against reference complexes.

## Leakage or bias risks

Potential training/test overlap in structural families unless homology and fold-level blocking are enforced.

## Toxicity/haemolysis relevance

None direct.

## Manufacturability relevance

Moderate: enables structural plausibility checks and may reduce unstable sequences.

## Agentic workflow relevance

Useful within a high-cost design-review branch.

## Limitations

Computationally expensive and likely hard to scale quickly in early iteration.

## What to implement

- Use for shortlist only, not raw batch generation.
- Keep a fallback to sequence-based generation if structure model confidence is low.

## What to avoid

- Do not make structure model outputs a hard acceptance criterion without assay context.

## Questions I should manually review

- Which structural quality metrics were most predictive in their ablations?
- What is runtime per candidate?
