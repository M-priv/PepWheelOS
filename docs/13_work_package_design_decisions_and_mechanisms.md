# Work Package Design Decisions & Architecture Index

**Document ID:** `DOC-ARCH-013`  
**Status:** Approved Reference Standard  
**Language Standard:** UK English  

This index provides direct links to the dedicated, deep-dive architectural and mathematical design documents for each completed work package in the Peptide Discovery Flywheel OS:

---

## Phase 3: Scientific Tooling, Epistemic Rigour & SRE Runtime

* 📄 [**`phase_3_wp_1_epistemic_rigour_and_domain_drc.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_3_wp_1_epistemic_rigour_and_domain_drc.md)  
  *Pillar 1:* Assume-Guarantee Contracts (`@enforce_contract`), Deterministic Biological DRC Invariants (`DRC-001` to `DRC-005`), and Adversarial Dialectical Committee (Advocate vs. Sceptic Agent with Dissensus Gating $\Delta_{\text{dissensus}}$).

* 📄 [**`phase_3_wp_2_sre_runtime_merkle_cas_and_ast_repair.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_3_wp_2_sre_runtime_merkle_cas_and_ast_repair.md)  
  *Pillar 4:* Merkle Content-Addressed Storage (`cas://<sha256>`), RFC 6902 JSON Patch deltas, Zero-LLM Deterministic AST Repair & Score Clamping, 3-State SRE Circuit Breaker, and 3-Tier Prefix-Invariant Prompts.

* 📄 [**`phase_3_wp_3_multi_objective_pareto_and_conformal_prediction.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_3_wp_3_multi_objective_pareto_and_conformal_prediction.md)  
  *Pillars 3 & 5A:* Avoiding the 1D Scalar Trap, NSGA-II Non-Dominated Pareto Sorting with Crowding Distance, and Split Conformal Prediction ($90\%$ distribution-free statistical coverage).

* 📄 [**`phase_3_wp_4_cli_integration_and_performance_architecture.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_3_wp_4_cli_integration_and_performance_architecture.md)  
  *Integration & Runtime:* Automated DRC Invariant Evaluation in Research DAG, Two-Language Symbiosis (Python orchestration + selective Rust PyO3 extensions), and Ponytail code-simplification standards.

---

## Phase 4: Experimental Feedback, Negative Data & Asynchronous Loop

* 📄 [**`phase_4_wp_1_dpp_sequence_diversity_repulsion.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_4_wp_1_dpp_sequence_diversity_repulsion.md)  
  *Pillar 2A:* Determinantal Point Process (DPP) $L$-Ensemble Matrix Formulation ($L = \text{diag}(q) K \text{diag}(q)$), 24-dimensional biophysical feature vectors, and Greedy Submodular MAP Selection in $\mathcal{O}(q^2 N)$ time.

* 📄 [**`phase_4_wp_2_async_bayesian_optimisation_and_fantasy_rollouts.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_4_wp_2_async_bayesian_optimisation_and_fantasy_rollouts.md)  
  *Pillar 2B:* The Physical Latency Mismatch, Mathematical Variance Independence Proof, Monte Carlo Fantasy Sampling ($M=32$), The 4 Physical Anchors, Automated MML Parameter Calibration, and Cholesky Numerical Stability (Eigenvalue Shift Theorem).

* 📄 [**`phase_4_wp_3_staggered_telemetry_ingestion.md`**](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/work_packages/phase_4_wp_3_staggered_telemetry_ingestion.md)  
  *Pillar 2C:* Three-Wave Staggered Telemetry Ingestion Timeline (Day 10 Crude LCMS $\to$ Day 18 Purified QC/DLS $\to$ Day 30 Bioassay SPR Kinetics), Monoisotopic Mass Accuracy Verification ($|M_{\text{obs}} - M_{\text{exp}}| \le 1.0\text{ Da}$), Tolerant CSV/JSON Parsers, and Lifecycle State Machine Transitions.

