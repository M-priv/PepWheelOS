# MoFormer: Multi-Objective Antimicrobial Peptide Generation Based on Conditional Transformer Joint Multi-modal Fusion Descriptor

## Metadata

Title: MoFormer: Multi-Objective Antimicrobial Peptide Generation Based on Conditional Transformer Joint Multi-modal Fusion Descriptor
Authors: Li Wang; Xiangzheng Fu; Jiahao Yang; Xinyi Zhang; Xiucai Ye; Yiping Liu; Tetsuya Sakurai; Xiangxiang Zeng
Year: 2024
arXiv ID: 2406.02610
URL: https://arxiv.org/abs/2406.02610
Module tags: module_5,module_4,module_2
Priority: useful_next

## Summary

MoFormer combines conditional transformer generation with multi-modal descriptors to create peptides targeting multiple properties simultaneously, enabling controlled multi-constraint synthesis proposals.

## Why this matters for the peptide flywheel

Useful for turning the generator from unconstrained language modeling into policy-aware optimization under your safety/manufacturability constraints.

## Dataset used

AMP datasets used for supervised multi-objective tuning; details need full-text confirmation.

## Method/model

Conditional transformer + fusion descriptors with multi-objective signal injection.

## Validation design

Ablation over conditional features and objective-conditioned generation quality.

## Leakage or bias risks

Potential leakage if descriptor/sequence splits are not homology-aware; include external split integrity checks.

## Toxicity/haemolysis relevance

Moderate to high: objective channel design includes bioactivity and adverse-effect axes.

## Manufacturability relevance

Low direct, medium via controlled generation constraints.

## Agentic workflow relevance

Can be invoked as generation primitive in design agent when objectives evolve per iteration.

## Limitations

Benchmark alignment and cost of training are uncertain from abstract-only capture.

## What to implement

- Encode each objective as bounded condition vectors instead of scalar weighting only.
- Add hard post-filters for forbidden motifs and length/synthesis constraints.

## What to avoid

- Avoid using raw objective outputs without uncertainty calibration.

## Questions I should manually review

- Which descriptors improved validity the most and why?
- What baseline splits were used in reported improvements?
