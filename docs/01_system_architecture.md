# System Architecture: Resilient Research OS

## High-level Architecture

```
User or Research Scientist
        │
        ▼
Campaign Workspace & Merkle Context Layer (cas://<sha256>)
        │
        ▼
4-Tier Epistemic Firewall (Syntax ──► Logic ──► Domain DRC ──► 4-Paradigm Dialectic)
        │
        ▼
Multi-Agent Execution Layer (3-Tier Prefix-Cached Prompts + SRE Circuit Breakers)
        │
        ▼
Multi-Objective Pareto & Conformal Gating (NSGA-II + Split Conformal Prediction)
        │
        ▼
Review-by-Exception Triage Workbench (Auto-Green 70% | Auto-Red 15% | Amber Triage 15%)
        │
        ▼
Asynchronous Wet-Lab Execution & Staggered Telemetry Ingestion (Crude LCMS ──► QC ──► Bioassays)
        │
        ▼
Decoupled Negative Data Learning & Causal Ontology Deconstruction
        │
        ▼
Overlapping Round Generation via Monte Carlo Fantasy Rollouts (X_pending)
```

## Core Storage & Data Objects

- `Target`: Target biology, binding sites, disease context, and assay options.
- `Hypothesis`: Mechanistic rationale and structural design constraints.
- `PeptideCandidate`: Sequence, modality, chemical modifications, predicted properties.
- `PendingEvaluationRecord`: In-flight synthesis/assay tracking with fantasy states.
- `MultiFidelityAssayReadout`: Multi-tier assay measurements with Tobit censoring tags.
- `CausalFailureAttribution`: Deconstructed motif failure modes mapped to ontology.
- `DecisionRecord`: Explicit human or automated governance decisions.
- `CompactContextEnvelope`: Merkle CAS references (`cas://`) and RFC 6902 JSON deltas.

## Resilient 5-Pillar Architectural Subsystems

### 1. Epistemic Rigor & Domain DRC (Pillar 1)
- **Assume-Guarantee Contracts**: Formal precondition/postcondition assertions (`contracts.py`).
- **Domain Biological DRC**: Hard chemical invariant checks (aspartimide, poly-hydrophobic collapse, extreme pI) run prior to model scoring (`domain_drc.py`).
- **Adversarial Dialectic Committee**: Advocate Agent vs. Sceptic Agent with Rule/SMT Arbiter (`dialectic.py`). Dissensus triggers discriminative wet-lab assay routing.

### 2. Asynchronous Pipelining & Multi-Fidelity BO (Pillar 2)
- **Determinantal Point Process (DPP)**: $L$-ensemble sequence diversity repulsion over ESM-2 embeddings (`dpp_sampler.py`).
- **Monte Carlo Fantasy Rollouts**: Asynchronous BO over pending in-flight synthesis points $X_{\text{pending}}$ (`async_bo.py`).
- **Staggered Telemetry Ingestion**: Day 10 Crude LCMS $\to$ Day 18 QC $\to$ Day 30 Bioassays (`result_ingestion.py`).

### 3. Decoupled Negative Data Learning (Pillar 3)
- **Decoupled Hurdle GPs**: Feasibility Classifier ($P(\text{Feasible} \mid x)$) strictly isolated from Potency Regressor ($f(x) \mid \text{Feasible}$) (`hurdle_models.py`).
- **Tobit Likelihood Engine**: Right-censored bioassay limits preserving boundary information without variance distortion (`tobit_gp.py`).
- **Causal Motif Deconstructor & Retroactive Sweeper**: Maps failures to `04_failure_ontology.md` and retroactively flags legacy DAG candidates (`ontology_sweeper.py`).

### 4. SRE Agent Runtime & Merkle CAS (Pillar 4)
- **Content-Addressed Storage (CAS)**: Immutable SHA-256 entity store (`cas://`) with RFC 6902 JSON Patch deltas (`cas_store.py`).
- **3-Tier Prefix-Invariant Caching**: [Tier 1: Static Rules] + [Tier 2: Campaign Target] + [Tier 3: Dynamic Candidate] for $100\%$ KV-cache reuse.
- **Localized AST Repair & 3-State Circuit Breakers**: Auto-context injection, subtree patching, and Dead-Letter Queue isolation (`circuit_breaker.py`).

### 5. Review-by-Exception & Apple HIG Scientist Triage (Pillar 5)
- **Tri-State Automated Funnel**: Auto-Green (70%), Auto-Red (15%), Amber Scientist Triage (15%) (`triage_engine.py`).
- **Multi-Objective Pareto Sorting**: NSGA-II non-dominated sorting and hypervolume clustering (`pareto_sort.py`).
- **Split Conformal Prediction**: Distribution-free $90\%$ coverage intervals (`conformal.py`).
- **Apple HIG Triage Workbench**: Glassmorphic UI with 3-level progressive disclosure (Orbit $\to$ Radar $\to$ Forensic AST Drawer) and keyboard-first navigation (`J/K/A/R`).

## Language & Performance Architecture

For detailed performance profiles and multi-language strategy, see [12_language_and_performance_architecture.md](docs/12_language_and_performance_architecture.md).
- **Python:** High-level orchestration, agent contracts, research DAG, and PyTorch/ESM-2 ML integration.
- **Rust (PyO3 / Maturin):** Selective acceleration for combinatorial sequence screening ($10^7+$ variants) and high-dimensional DPP sampling.


