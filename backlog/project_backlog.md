# Project Backlog

## Phase 3 (Immediate: Scientific Tooling, Epistemic Rigor & SRE Runtime)

- [ ] **Pillar 1: Contracts & Biological DRC**
  - [ ] Implement `@enforce_contract` Assume-Guarantee decorators (`src/peptide_flywheel/contracts.py`).
  - [ ] Implement Biological Design Rule Checking engine for SPPS aggregation, aspartimide, and pI (`src/peptide_flywheel/domain_drc.py`).
  - [ ] Implement Adversarial Dialectical Committee (Advocate vs. Sceptic Agent) with Rule Arbiter (`src/peptide_flywheel/dialectic.py`).
- [ ] **Pillar 4: SRE Runtime & Storage**
  - [ ] Implement Content-Addressed Storage (`cas://<sha256>`) and JSON Patch deltas (`src/peptide_flywheel/cas_store.py`).
  - [ ] Reorganize prompt templates into 3-tier prefix-invariant KV-cached prompts (`src/peptide_flywheel/prompt_pipeline.py`).
  - [ ] Implement localized AST subtree repair and deterministic context injection (`src/peptide_flywheel/ast_repair.py`).
  - [ ] Implement 3-state SRE circuit breaker and Dead-Letter Queue (`src/peptide_flywheel/circuit_breaker.py`).
- [ ] **Pillars 3 & 5A: Multi-Objective Pareto & Conformal Bounds**
  - [ ] Implement NSGA-II non-dominated sorting and hypervolume diversity clustering (`src/peptide_flywheel/pareto_sort.py`).
  - [ ] Implement Split Conformal Prediction intervals ($90\%$ coverage bounds) (`src/peptide_flywheel/conformal.py`).

## Phase 4 (Next: Experimental Feedback & Asynchronous Loop)

- [ ] **Pillar 2: Async BO & DPP Diversity**
  - [ ] Implement Determinantal Point Process (DPP) sequence diversity repulsion sampler (`src/peptide_flywheel/dpp_sampler.py`).
  - [ ] Implement Asynchronous Bayesian Optimization with Monte Carlo fantasy rollouts over $X_{\text{pending}}$ (`src/peptide_flywheel/async_bo.py`).
  - [ ] Implement multi-stage staggered telemetry ingestion (Crude LCMS -> QC Solubility -> Bioassays) (`src/peptide_flywheel/result_ingestion.py`).
- [ ] **Pillar 3: Decoupled Negative Data & Causal Attribution**
  - [ ] Implement Decoupled Hurdle GP ($P(\text{Feasible} \mid x) \times f_{\text{potency}}(x \mid \text{Feasible})$) (`src/peptide_flywheel/hurdle_models.py`).
  - [ ] Implement Tobit right-censored likelihood engine for assay detection floor/ceiling limits (`src/peptide_flywheel/tobit_gp.py`).
  - [ ] Implement causal motif SPPS/assay failure deconstruction mapped to `04_failure_ontology.md` (`src/peptide_flywheel/causal_attribution.py`).
  - [ ] Implement Retroactive Invariant Sweeper for historical DAG re-evaluation (`src/peptide_flywheel/ontology_sweeper.py`).

## Phase 5 (Later: Portfolio & Apple HIG Scientist Triage Workbench)

- [ ] **Pillar 5B: Triage Engine & Apple HIG UI**
  - [ ] Implement Review-by-Exception tri-state automated gating engine (Auto-Green 70%, Auto-Red 15%, Amber Triage 15%) (`src/peptide_flywheel/triage_engine.py`).
  - [ ] Build Apple HIG-inspired glassmorphic scientist triage UI (`src/peptide_flywheel/ui/`) with 3-level progressive disclosure (Orbit -> Radar -> Forensic AST Drawer).
  - [ ] Implement keyboard-first power triage (`J/K/A/R`) CLI and web server launcher (`scripts/run_triage_workbench.py`).
  - [ ] Run full reproducible 3-round asynchronous campaign demo.

