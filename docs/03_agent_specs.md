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

## Red-Team Agent

Purpose:
Attack the strongest candidates before money is spent on testing.

Outputs:
- Reasons candidate may fail
- Assay artefact risks
- Model overconfidence risks
- Alternative explanations
- Minimum evidence needed to proceed

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

## Learning Agent

Purpose:
Update the research graph after results arrive.

Outputs:
- Prediction versus outcome comparison
- Failure mode assignment
- Revised design heuristics
- Next-round recommendation
