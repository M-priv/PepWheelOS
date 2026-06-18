# Roadmap

**Current slice: Phase 2 (Semi-automated agents)**

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
- [x] Data ingestion governance and split provenance from literature (`LIT-AMP-001`, `LIT-AMP-002`, `LIT-AMP-003`)
  - [x] Ingestion contract checks (`dataset` schema + identifier/sequence validation, duplicate IDs, required columns)
  - [x] Split manifest provenance capture (`dataset_id`, `split_method`, `split_column`, tags, guard settings)
  - [x] Split-aware leakage checks (exact/near-duplicate guards, truncated pairwise scan)
  - [x] Workflow preflight integration (`seed_dataset_path` + manifest wiring + governance report output)

### Phase 1: Manual flywheel (current)

- [x] Manual round runner with target + hypothesis + candidates (`src/peptide_flywheel/workflows.py`)
- [x] CLI runner for local manual round execution (`scripts/run_manual_flywheel_round.py`)
- [x] Heuristic manufacturability scoring (`src/peptide_flywheel/scoring.py`)
- [x] Candidate card / batch summary markdown artifacts (`src/peptide_flywheel/reporting.py`)
- [x] JSONL/JSON persistence + validation hardening and strict/lenient modes (`src/peptide_flywheel/storage.py`, tests)
- [x] Manual dossier + 10-to-30 real candidate cards using templates (`examples`/`templates`)
- [x] CRO pack and red-team critiques
  - [x] Added CRO packs for high-priority seed candidates.
  - [x] Added red-team critique files for same candidates.
- [x] Simulated result ingestion + failure classification
  - [x] Added markdown and JSON result parser with validation and raw-file capture.
  - [x] Added heuristic failure-mode classifier aligned to ontology.
  - [x] Added simulated result ingestion script and example campaign outputs.
  - [x] Added result-to-candidate review step (`scripts/run_result_review.py`) to apply status transitions and persist decision records.
  - [x] Added campaign-DAG merge in review loop when `--base-dag-json` is provided.
  - [x] Added campaign close-loop outputs:
    - `closed_loop_recommendations.json`
    - `campaign_recommendation_plan.json`
    - `next_round_plan.json`
    - `campaign_decision.json`.

### Phase 2: Semi-automated agents

- [x] CLI/JSON schema validation hooks
- [x] Structured prompt pipelines for target dossier, candidate cards, red-team, assay pack
- [x] Batch import/export and report generator
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
