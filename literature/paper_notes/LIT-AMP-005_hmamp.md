# HMAMP: Hypervolume-Driven Multi-Objective Antimicrobial Peptides Design

## Metadata

Title: HMAMP: Hypervolume-Driven Multi-Objective Antimicrobial Peptides Design
Authors: Li Wang; Yiping Li; Xiangzheng Fu; Xiucai Ye; Junfeng Shi; Gary G. Yen; Xiangxiang Zeng
Year: 2024
arXiv ID: 2405.00753
URL: https://arxiv.org/abs/2405.00753
Module tags: module_5,module_4,module_6
Priority: useful_next

## Summary

HMAMP frames AMP design as multi-objective optimization and explicitly tracks Pareto volume across potency, toxicity, and hemolysis, giving a practical way to avoid single-metric over-optimization.

## Why this matters for the peptide flywheel

It directly informs scoring-weight strategy and candidate selection for diverse design rounds.

## Dataset used

AMP training data used for multi-attribute optimization; exact partitioning requires manual review.

## Method/model

Hypervolume-based RL/optimization loop with objective-conditioned generation and scoring.

## Validation design

Comparisons across multiple baselines on activity and toxicity metrics, with Pareto-front quality reporting.

## Leakage or bias risks

If objective labels overlap across folds, the optimization may overfit; strict leakage audits still required.

## Toxicity/haemolysis relevance

High: both are explicit optimization objectives.

## Manufacturability relevance

Medium: supports objective weighting to reduce manufacturability-risky candidates indirectly.

## Agentic workflow relevance

Medium: design policy can be executed in a controller agent loop.

## Limitations

Unknown exact assay normalization and curation details from abstract summary.

## What to implement

- Use hypervolume score as one ranking axis for candidate batches.
- Separate hard constraints (toxicity/hemolysis) from soft constraints (hydrophobicity).

## What to avoid

- Do not optimize all objectives with equal weight; use policy-specific tradeoff templates.

## Questions I should manually review

- Is dataset split consistent with your inclusion/exclusion protocol?
- How are contradictory labels handled when both toxic and low-MIC evidence exist?
