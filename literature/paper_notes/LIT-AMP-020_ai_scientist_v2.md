# The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search

## Metadata

Title: The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search
Authors: Yutaro Yamada et al.
Year: 2025
arXiv ID: 2504.08066
URL: https://arxiv.org/abs/2504.08066
Module tags: module_8,module_7,module_3
Priority: useful_next

## Summary

AI Scientist-v2 pushes fully-automated cycles of hypothesis generation, experiment planning, execution, interpretation, and iteration using tree-search for controlled exploration.

## Why this matters for the peptide flywheel

Strong template for DMTL execution: especially iteration scheduling, experiment planning, and stopping criteria.

## Dataset used

Research planning workloads and benchmark tasks; not AMP-specific.

## Method/model

Agentic tree-search controller with experiment manager and evidence scoring.

## Validation design

Scenario-based evaluation across synthetic and text/code-heavy benchmarks.

## Leakage or bias risks

Potential overfitting to benchmark prompts and false confidence in unverified claims.

## Toxicity/haemolysis relevance

No direct models.

## Manufacturability relevance

No direct chemistry model.

## Agentic workflow relevance

High for pipeline orchestration design and rollback policies.

## Limitations

Cross-domain adaptation required for peptide biology and lab workflows.

## What to implement

- Use tree-search scheduling with explicit budget and hard safety budget ceilings.
- Force periodic manual checkpoint checkpoints in high-risk rounds.

## What to avoid

- Avoid fully autonomous branch expansion without resource constraints.

## Questions I should manually review

- Can the planning node integrate your assay costs and assay queue constraints?
- What quality bar triggers branch pruning?
