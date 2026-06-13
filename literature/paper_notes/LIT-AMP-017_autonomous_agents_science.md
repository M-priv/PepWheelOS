# Autonomous Agents for Scientific Discovery: Orchestrating Scientists, Language, Code, and Physics

## Metadata

Title: Autonomous Agents for Scientific Discovery: Orchestrating Scientists, Language, Code, and Physics
Authors: Lianhao Zhou et al.
Year: 2025
arXiv ID: 2510.09901
URL: https://arxiv.org/abs/2510.09901
Module tags: module_8,module_7
Priority: useful_next

## Summary

The paper proposes role decomposition where hypothesis agents, coding agents, and validation agents form a coordinated loop for scientific workflows.

## Why this matters for the peptide flywheel

Gives a clear separation of responsibilities between generator, checker, red-team, and synthesizer-facing agents.

## Dataset used

Not directly dataset-specific.

## Method/model

System design + orchestration strategy.

## Validation design

Case-study style evaluation across scientific workflows.

## Leakage or bias risks

Agent overreach can propagate single-agent errors; explicit independence constraints are required.

## Toxicity/haemolysis relevance

None direct.

## Manufacturability relevance

None direct, but useful for process design.

## Agentic workflow relevance

High for role design and escalation structure.

## Limitations

No direct AMP-specific implementation details.

## What to implement

- Define strict role contracts with required input/output schema.
- Add cross-agent contradiction checks before synthesis handoff.

## What to avoid

- Avoid single-point planning where one agent writes, scores, and approves candidates.

## Questions I should manually review

- How often does cross-role disagreement improve final scientific validity?
- Which roles are unnecessary in early prototypes?
