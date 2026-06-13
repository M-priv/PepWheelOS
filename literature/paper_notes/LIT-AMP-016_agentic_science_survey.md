# From AI for Science to Agentic Science: A Survey on Autonomous Scientific Discovery

## Metadata

Title: From AI for Science to Agentic Science: A Survey on Autonomous Scientific Discovery
Authors: Jiaqi Wei et al.
Year: 2025
arXiv ID: 2508.14111
URL: https://arxiv.org/abs/2508.14111
Module tags: module_8,module_7,module_1
Priority: useful_next

## Summary

This survey maps capability components and workflow stages for autonomous scientific systems, including planning, reasoning, verification, governance, and reproducibility expectations.

## Why this matters for the peptide flywheel

Provides architectural vocabulary for implementing agent contracts, evidence quality levels, and control planes.

## Dataset used

Not dataset-specific.

## Method/model

Cross-study survey + framework taxonomy.

## Validation design

Comparative framework analysis against representative autonomous systems.

## Leakage or bias risks

Survey can over-generalize across domains; transfer to peptide discovery requires explicit adaptation.

## Toxicity/haemolysis relevance

Low direct.

## Manufacturability relevance

Low direct.

## Agentic workflow relevance

High: governance and reliability guidance for orchestration and escalation.

## Limitations

No direct benchmarks for your exact AMP stack.

## What to implement

- Add explicit stage labels and confidence levels per agent output.
- Encode manual review gates where model confidence is low.

## What to avoid

- Avoid broad claims from this paper as implementation guarantees.

## Questions I should manually review

- Which failure patterns are most common in production autonomous systems?
- How to enforce accountability across tool calls?
