# Zero-Shot Cyclic Peptide Design via Composable Geometric Constraints

## Metadata

Title: Zero-Shot Cyclic Peptide Design via Composable Geometric Constraints
Authors: Dapeng Jiang; Xiangzhe Kong; Jiaqi Han; Mingyu Li; Rui Jiao; Wenbing Huang; Stefano Ermon; Jianzhu Ma; Yang Liu
Year: 2025
arXiv ID: 2507.04225
URL: https://arxiv.org/abs/2507.04225
Module tags: module_9,module_5,module_6
Priority: useful_now

## Summary

The work proposes zero-shot cyclic peptide generation using composable geometric constraints, useful for cyclic chemotypes where paired cyclic training data is scarce.

## Why this matters for the peptide flywheel

Directly informs cyclic branch behavior and could enable constrained generation without expensive dedicated dataset re-trains.

## Dataset used

Cyclic peptide structure references and geometric templates; limited low-data setting emphasized.

## Method/model

Constraint-conditioned geometric generation with multiple cyclization strategy composition.

## Validation design

Ablation and strategy-comparison on structure quality and success-rate metrics.

## Leakage or bias risks

Constraint templates may encode biases toward known chemotypes; monitor novelty and scaffold diversity.

## Toxicity/haemolysis relevance

Indirect.

## Manufacturability relevance

High for cyclic manufacturability and cyclization feasibility assumptions.

## Agentic workflow relevance

Useful for task planner to route cyclic cases through special generation policy.

## Limitations

Abstract-level claims only; synthesis feasibility still uncertain.

## What to implement

- Add a dedicated cyclic path with geometry guardrails and ring-closure checks.
- Penalize excessive ring strain proxies from generated structures.

## What to avoid

- Avoid interpreting zero-shot success as full generalization without experimental confirmation.

## Questions I should manually review

- Which constraints reduce false-positives most?
- What are false closure patterns and byproduct risks?
