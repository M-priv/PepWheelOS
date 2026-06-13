# Why LLMs Aren't Scientists Yet: Failure Modes, Limits, and Opportunities in Autonomous Discovery

## Metadata

Title: Why LLMs Aren't Scientists Yet: Failure Modes, Limits, and Opportunities in Autonomous Discovery
Authors: Sasha Saito; Emily R. Smith; Kenji Tanaka
Year: 2026
arXiv ID: 2601.03315
URL: https://arxiv.org/abs/2601.03315
Module tags: module_7,module_8,module_3
Priority: useful_next

## Summary

This paper catalogs recurring failure modes in autonomous scientific workflows and argues for robust failure taxonomy, uncertainty expression, and human-overridden safety checkpoints.

## Why this matters for the peptide flywheel

It aligns directly with your failure ontology and red-team requirements and can prevent over-automation.

## Dataset used

Autonomous discovery case studies and synthetic evaluations.

## Method/model

Analytical framework and taxonomy, not a single algorithmic model.

## Validation design

Comparative study of autonomous attempt quality and failure frequencies.

## Leakage or bias risks

Failure taxonomies may depend on a small set of tasks; treat as heuristic guidance only.

## Toxicity/haemolysis relevance

No direct.

## Manufacturability relevance

No direct.

## Agentic workflow relevance

Very high for ontology and escalation policy design.

## Limitations

Need manual verification for transfer to your domain.

## What to implement

- Expand your failure ontology to include data leakage, assay-interference, and agent overconfidence buckets.
- Require explicit "what would falsify this claim" outputs.

## What to avoid

- Avoid removing uncertainty handling because a loop appears successful once.

## Questions I should manually review

- Which failure classes appear first in your first 50 runs?
- What escalation rules should block synthesis budget release?
