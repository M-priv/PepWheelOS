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

Agent outputs should be checked through the contract validator before they are accepted into a campaign. A valid agent handoff has:
- a source prompt packet
- a JSON-only response
- schema-valid output for the requested artifact
- identifiers that match the source target, hypothesis, candidate, campaign and run context
- warnings for missing uncertainty, risk, evidence or control fields
- a retry packet when repairable failures are found

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

## Adversarial Dialectic Committee (Advocate vs. Sceptic Agent)

Purpose:
Eliminate shared cognitive blind spots and sycophantic convergence via dialectical falsification.

### Advocate Agent
- **Utility Function:** Build the strongest structural and biological affinity case for candidate.
- **Outputs:** Proposed binding mechanism, interface contacts, target fit rationale, predicted affinity.

### Sceptic / Red-Team Agent
- **Utility Function:** Formulate explicit falsification hypotheses and identify failure modes.
- **Outputs:** Structural clash liabilities, SPPS aggregation risks, assay artifact risks, unaddressed unknowns, hard-stop recommendations.

### Rule & SMT Arbiter
- **Utility Function:** Adjudicate between Advocate and Sceptic using physical invariants (Domain DRC) and empirical historical benchmarks.
- **Outputs:** Adjudication score, dissensus metric ($\Delta_{\text{dissensus}}$), routing recommendation (`SYNTHESIS_PIPELINE`, `ACTIVE_LEARNING_DISCRIMINATIVE_ASSAY`, or `REJECT_WITH_FAILURE_MEMORY`).

## Tri-State Triage Gating Agent

Purpose:
Execute automated review-by-exception to protect human scientists from review fatigue.

Outputs:
- Gating classification:
  - `AUTO_GREEN`: High potency, zero risk flags, high conformal confidence $\to$ auto-queued for synthesis with audit log.
  - `AUTO_RED`: Hard-stop chemical/synthesis liabilities $\to$ auto-rejected with ontology attribution.
  - `AMBER_TRIAGE`: High-uncertainty, high-novelty, or conflicting Pareto trade-offs $\to$ routed to Apple HIG triage workbench.
- Multi-objective Pareto rank and hypervolume contribution score.
- Conformal prediction intervals ($90\%$ coverage bounds).

## Minimum retry policy:
- Parse and validate every agent response before accepting it.
- Retry only repairable contract failures such as invalid JSON, schema errors or identifier mismatch.
- Stop after the configured maximum attempts and require human review.
- Preserve the original prompt packet, failed output, validation report and retry packet as artifacts.
- Do not treat a successful retry as scientific evidence; it only proves contract compliance.

