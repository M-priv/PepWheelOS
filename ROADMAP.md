# Roadmap

**Current slice: Phase 1 (Manual flywheel)**

## Phase 0: Scaffold and domain setup

Goal:
Create a clean structure for the system and define schemas before writing complex code.

Deliverables:
- Research object schemas
- Candidate card schema
- Failure ontology
- Agent protocols
- Example campaign folder
- Manual data-entry workflow

## Phase 1: Manual flywheel

Goal:
Make the system useful even before automation.

Deliverables:
- Manually populated target dossier
- 10 to 30 peptide candidate cards
- Manufacturability scores
- Red-team critiques
- Assay plan
- Simulated results and failure classification

## Phase 2: Semi-automated agents

Goal:
Use LLMs to populate structured records, but keep humans in control.

Deliverables:
- Target dossier generation prompt
- Candidate-card generation prompt
- Red-team prompt
- Assay-pack generation prompt
- Structured JSON output validation

## Phase 3: Scientific tooling integration

Goal:
Connect specialist tools and models.

Potential integrations:
- RDKit or Biopython for molecular/sequence descriptors
- Protein language model embeddings
- Structure prediction outputs
- Docking or structural scoring workflows
- Molecular dynamics analysis outputs
- Toxicity, solubility and aggregation predictors

## Phase 4: Experimental feedback loop

Goal:
Ingest CRO/CDMO and assay outputs into the research graph.

Deliverables:
- Synthesis result parser
- Assay result schema
- Failure taxonomy mapping
- Next-round design recommendation engine

## Phase 5: Portfolio and venture demo

Goal:
Show a complete end-to-end campaign.

Deliverables:
- One public demo campaign with safe/non-sensitive target
- Technical report
- Architecture diagram
- Investor-readable summary
- GitHub repo with reproducible examples

## Slice assignment for implementations (ordered)

### Phase 0: Scaffold and domain setup

- [x] Research object schema baseline (`src/peptide_flywheel/models.py`)
- [x] Candidate status/state and reporting primitives
- [x] Candidate cards and failure ontology scaffolding (templates/docs)
- [x] DAG storage + integrity checks (`src/peptide_flywheel/dag.py`)
- [ ] Data ingestion governance and split provenance from literature (`LIT-AMP-001`, `LIT-AMP-002`, `LIT-AMP-003`)

### Phase 1: Manual flywheel (current)

- [x] Manual round runner with target + hypothesis + candidates (`src/peptide_flywheel/workflows.py`)
- [x] CLI runner for local manual round execution (`scripts/run_manual_flywheel_round.py`)
- [x] Heuristic manufacturability scoring (`src/peptide_flywheel/scoring.py`)
- [x] Candidate card / batch summary markdown artifacts (`src/peptide_flywheel/reporting.py`)
- [x] JSONL/JSON persistence + validation hardening and strict/lenient modes (`src/peptide_flywheel/storage.py`, tests)
- [ ] Manual dossier + 10-to-30 real candidate cards using templates (`examples`/`templates`)
- [ ] CRO pack and red-team critiques
- [ ] Simulated result ingestion + failure classification

### Phase 2: Semi-automated agents

- [ ] CLI/JSON schema validation hooks
- [ ] Structured prompt pipelines for target dossier, candidate cards, red-team, assay pack
- [ ] Batch import/export and report generator
- [ ] Active-learning simulator + prompt-driven scoring summaries
- [ ] Agent contract hardening and retry policy (`LIT-AMP-014`, `LIT-AMP-019`, `LIT-AMP-021`)

### Phase 3: Scientific tooling integration

- [ ] Sequence/property tool layer (structure embeddings, descriptors) from generated candidates
- [ ] Pluggable predictor layer: hemolysis/toxicity/regression style outputs (`LIT-AMP-004`, `LIT-AMP-007`, `LIT-AMP-008`)
- [ ] Multi-objective ranking templates with Pareto/hypervolume policy (`LIT-AMP-005`, `LIT-AMP-006`, `LIT-AMP-015`)
- [ ] Binder/cyclic route feasibility checks (`LIT-AMP-010`, `LIT-AMP-011`, `LIT-AMP-012`)
- [ ] DAG visibility: richer agent graph outputs and tool-call provenance

### Phase 4: Experimental feedback loop

- [ ] Vendor/CDMO report parser and normalized assay result schema
- [ ] Failure mode mapping loop against existing ontology (`docs/04_failure_ontology.md`)
- [ ] Closed-loop recommendations from assay outcomes
- [ ] Uncertainty calibration / contradiction logging (`LIT-AMP-021`)

### Phase 5: Portfolio and venture demo

- [ ] Full reproducible campaign using one safe target
- [ ] Portfolio-style decision record + technical story deck
- [ ] Public-facing architecture + governance summary
- [ ] Dashboard-style campaign explorer
