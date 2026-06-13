# MAC-AMP: A Closed-Loop Multi-Agent Collaboration System for Multi-Objective Antimicrobial Peptide Design

## Metadata

Title: MAC-AMP: A Closed-Loop Multi-Agent Collaboration System for Multi-Objective Antimicrobial Peptide Design
Authors: Gen Zhou; Sugitha Janarthanan; Lianghong Chen; Pingzhao Hu
Year: 2026
arXiv ID: 2602.14926
URL: https://arxiv.org/abs/2602.14926
Module tags: module_5,module_8,module_3
Priority: must_read_now

## Summary

MAC-AMP proposes a multi-agent system with simulated peer-review and feedback loops to jointly optimize antimicrobial activity, hemolysis, and novelty across candidate design cycles.

## Why this matters for the peptide flywheel

It is the nearest AMP-focused design for your closed-loop architecture and can guide role definitions, iteration policies, and quality gates.

## Dataset used

AMP training and benchmark datasets plus synthetic scoring runs; exact splits need full-text review.

## Method/model

Multi-agent co-design with evaluator agents, reward shaping, and reviewer feedback simulation.

## Validation design

Closed-loop improvements across iterations compared to baseline generators.

## Leakage or bias risks

Cross-agent knowledge sharing can cause shared blind spots; enforce independent checks with seed-specific holdouts.

## Toxicity/haemolysis relevance

High due to explicit multi-objective design around safety.

## Manufacturability relevance

Indirect through objective extension.

## Agentic workflow relevance

Very high; this is the anchor paper for agent choreography.

## Limitations

Reproducibility and reward calibration details need manual extraction from full text.

## What to implement

- Add reviewer and challenger agents distinct from generator agents.
- Track per-round objective deltas and rollback criteria.

## What to avoid

- Do not let a single evaluator dominate candidate acceptance.

## Questions I should manually review

- Is simulated peer-review statistically robust or mostly prompt-based?
- What stopping criteria are used for loop termination?
