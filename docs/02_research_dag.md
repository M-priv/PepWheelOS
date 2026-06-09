# Research DAG

## Why DAG-first?

A peptide project is not a linear document. It is a branching sequence of hypotheses, designs, tests and revisions.

A Directed Acyclic Graph lets you capture:

- Which hypothesis produced which design batch
- Which model run generated which candidates
- Which candidates were selected for testing
- Which results invalidated which assumptions
- Which failures drove the next design round

## Node types

### Target
A protein, receptor, pathway component, pathogen component or delivery target.

### Hypothesis
A falsifiable scientific claim.

Example:
A constrained cyclic peptide mimicking interface motif X may bind target surface Y with improved protease stability versus an unconstrained linear peptide.

### DesignBatch
A set of peptide candidates generated under one design strategy.

### PeptideCandidate
A sequence or modified peptide with structured metadata.

### PredictionRun
Any computational evaluation: property prediction, structure prediction, docking, MD analysis, toxicity prediction or solubility prediction.

### ExperimentalResult
Any wet-lab, CRO, CDMO or analytical outcome.

### FailureMode
A structured reason for failure.

### DecisionRecord
A human or agent-assisted decision that affects the campaign.

## Edge types

- supports
- rejects
- generated
- evaluated_by
- selected_for
- failed_due_to
- updated_by
- next_round_from
