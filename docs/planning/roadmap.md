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
- [x] Active-learning simulator + prompt-driven scoring summaries
  - [x] Added deterministic next-batch ranking over candidate records.
  - [x] Added prompt packet for scoring-summary review.
  - [x] Added CLI, markdown report, JSON plan/rankings and DAG output.
- [x] Agent contract hardening and retry policy (`LIT-AMP-014`, `LIT-AMP-019`, `LIT-AMP-021`)
  - [x] Added prompt-packet contract validation for agent JSON outputs.
  - [x] Added context ID checks against source packet inputs.
  - [x] Added deterministic retry packet generation for repairable failures.
  - [x] Added CLI and tests for contract evaluation.

### Phase 3: Scientific Tooling, Epistemic Rigor & SRE Runtime

- [ ] **Pillar 1: 4-Tier Epistemic Firewall & Domain DRC**
  - [ ] Assume-Guarantee contract decorators (`src/peptide_flywheel/contracts.py`)
  - [ ] Biological Design Rule Checking (DRC) engine for hard chemical/synthesis invariants (`src/peptide_flywheel/domain_drc.py`)
  - [ ] Adversarial Dialectical Committee (Advocate vs. Sceptic Agent) with Rule Arbiter (`src/peptide_flywheel/dialectic.py`)
  - [ ] Dissensus-driven active learning routing for engine disagreement (`LIT-AMP-021`)
- [ ] **Pillar 4: SRE Agent Runtime & Content-Addressed Storage**
  - [ ] Content-Addressed Storage (`cas://<sha256>`) and JSON Patch delta encoder (`src/peptide_flywheel/cas_store.py`)
  - [ ] 3-Tier Prefix-Invariant KV-cache compliant prompt architecture (`src/peptide_flywheel/prompt_pipeline.py`)
  - [ ] Localized AST subtree repair and deterministic context injection (`src/peptide_flywheel/ast_repair.py`)
  - [ ] 3-State SRE circuit breaker, concurrency bulkheads, and Dead-Letter Queue (`src/peptide_flywheel/circuit_breaker.py`)
- [ ] **Pillars 3 & 5A: Multi-Objective Pareto Sorting & Conformal Prediction**
  - [ ] NSGA-II non-dominated sorting and hypervolume diversity clustering (`src/peptide_flywheel/pareto_sort.py`)
  - [ ] Split Conformal Prediction intervals ($90\%$ coverage bounds) for property surrogates (`src/peptide_flywheel/conformal.py`)

### Phase 4: Experimental Feedback, Negative Data & Asynchronous Loop

- [ ] **Pillar 2: Asynchronous Pipelining & Multi-Fidelity Batch BO**
  - [ ] Determinantal Point Process (DPP) $L$-ensemble sequence diversity repulsion sampler (`src/peptide_flywheel/dpp_sampler.py`)
  - [ ] Asynchronous Bayesian Optimization with Monte Carlo fantasy rollouts over $X_{\text{pending}}$ (`src/peptide_flywheel/async_bo.py`)
  - [ ] Multi-stage staggered telemetry ingestion (Day 10 Crude LCMS -> Day 18 QC -> Day 30 Bioassays) (`src/peptide_flywheel/result_ingestion.py`)
- [ ] **Pillar 3: Decoupled Negative Data Learning & Causal Attribution**
  - [ ] Decoupled Hurdle GP Feasibility Classifier ($P(\text{Feasible} \mid x) \times f_{\text{potency}}(x \mid \text{Feasible})$) (`src/peptide_flywheel/hurdle_models.py`)
  - [ ] Tobit right-censored likelihood engine for assay detection floor/ceiling limits (`src/peptide_flywheel/tobit_gp.py`)
  - [ ] Causal motif failure deconstruction mapped to `04_failure_ontology.md` (`src/peptide_flywheel/causal_attribution.py`)
  - [ ] Retroactive Invariant Sweeper for historical DAG re-evaluation (`src/peptide_flywheel/ontology_sweeper.py`)

### Phase 5: Portfolio & Apple HIG Scientist Triage Workbench

- [ ] **Pillar 5B: Review-by-Exception & Apple HIG Triage UI**
  - [ ] Review-by-Exception tri-state automated gating engine (Auto-Green 70%, Auto-Red 15%, Amber Triage 15%) (`src/peptide_flywheel/triage_engine.py`)
  - [ ] Apple HIG-inspired glassmorphic scientist triage interface (`src/peptide_flywheel/ui/`) with 3-level progressive disclosure (Orbit -> Radar -> Forensic AST Drawer)
  - [ ] Keyboard-first power triage (`J/K` navigate, `A` advance, `R` reject with ontology code `1-4`, `Space` forensic drawer) (`scripts/run_triage_workbench.py`)
  - [ ] Full reproducible 3-round asynchronous campaign demo with investor/technical report

