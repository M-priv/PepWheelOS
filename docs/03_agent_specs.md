# Agent Specifications

## General agent rules

Every agent must:

1. State its task.
2. Read existing structured context.
3. Produce structured outputs.
4. Record uncertainty.
5. Record assumptions.
6. Identify what would falsify its output.
7. Avoid making unverified clinical or experimental claims.

## Target Intelligence Agent

Purpose:
Create a structured target dossier.

Inputs:
- Target name
- Disease or use case
- Desired peptide modality
- Available literature or database records

Outputs:
- Biological rationale
- Known binding regions
- Existing ligands or competitors
- Structural data availability
- Assay options
- Risks and unknowns
- Candidate design hypotheses

## Design Orchestrator Agent

Purpose:
Choose a design route and produce candidate batches.

Design routes:
- Linear binder
- Cyclic peptide
- Motif-constrained peptide
- Interface mimic
- Antimicrobial peptide
- Delivery ligand
- Modified known binder

Outputs:
- Design strategy
- Candidate list
- Rationale per candidate
- Required downstream scoring
- Multi-objective tradeoff rationale (`LIT-AMP-005`, `LIT-AMP-006`, `LIT-AMP-007`, `LIT-AMP-015`)

## Manufacturability Agent

Purpose:
Score candidates for development and synthesis risk.

Outputs:
- Solubility risk
- Aggregation risk
- Synthesis difficulty
- Purification risk
- Modification complexity
- Stability liabilities
- Overall manufacturability score
- Hard-stop reasons
- Suggested mitigations (`LIT-AMP-004`, `LIT-AMP-007`, `LIT-AMP-012`)

## Red-Team Agent

Purpose:
Attack the strongest candidates before money is spent on testing.

Outputs:
- Reasons candidate may fail
- Assay artefact risks
- Model overconfidence risks
- Alternative explanations
- Minimum evidence needed to proceed
- Failure bucket assignments (`LIT-AMP-021`, `LIT-AMP-018`)

## Assay Planning Agent

Purpose:
Convert hypotheses into validation plans.

Outputs:
- Assay menu
- Controls
- Readouts
- Acceptance criteria
- Rejection criteria
- Priority order
- Homology-aware split plan for local re-evals (`LIT-AMP-003`, `LIT-AMP-021`)

## Learning Agent

Purpose:
Update the research graph after results arrive.

Outputs:
- Prediction versus outcome comparison
- Failure mode assignment
- Revised design heuristics
- Next-round recommendation

## Binder Agent

Purpose:
Route and design binder-specific peptide candidates.

Outputs:
- Target-site candidate list
- Complex-aware sequence/structure suggestions
- Cyclisation feasibility notes
- Confidence score and failure-mode rationale (`LIT-AMP-010`, `LIT-AMP-011`, `LIT-AMP-012`, `LIT-AMP-013`, `LIT-AMP-014`)

## MCP Orchestration Agent

Purpose:
Coordinate tool calls, retries, and provenance capture.

Outputs:
- Planned tool graph and retry policy
- State snapshots
- Confidence-aware completion status
- Failed action retries and evidence trails (`LIT-AMP-014`, `LIT-AMP-019`)
