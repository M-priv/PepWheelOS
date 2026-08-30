# Phase 4 — Work Package 3: Staggered Multi-Stage Telemetry Ingestion (Pillar 2C)

**Module Location:** `src/peptide_flywheel/telemetry_ingestion.py`  
**Test Suite:** `tests/test_telemetry_ingestion.py`  
**Language Standard:** UK English  

---

## 1. Executive Summary & First-Principles Problem

In high-throughput peptide discovery, wet-lab results from contract research organisations (CROs) and CDMOs do **not** arrive as a single monolithic block on Day 30. Instead, experimental measurements arrive in **three distinct waves**:

```
Day 0                  Day 10 (Stage 1)              Day 18 (Stage 2)             Day 30 (Stage 3)
  │                           │                             │                            │
  ▼                           ▼                             ▼                            ▼
Orders Sent            Crude LCMS QC                 Purified QC & DLS            SPR & Bioassays
to CDMO/CRO            (Purity & Yield mg)           (Solubility & Aggregation)   (Kd, IC50, Kinetics)
                       Updates Feasibility           Updates Formulation          Collapses Fantasy GP
                       GP 20 Days Early!             Liability Models             to Exact Ground Truth
```

### The Problem:
* Naive computational platforms wait until Day 30 before ingesting any data.
* If a peptide suffered an intractable synthesis drop-out on Day 8 (e.g. base-catalysed aspartimide cyclisation or resin fouling), the computational team continues to treat it as an active in-flight lead for another 22 days, designing redundant follow-up mutations in Monte Carlo fantasy BO.

### The Solution (Pillar 2C):
An asynchronous, multi-stage telemetry ingestion engine that ingests experimental data at each physical milestone, updating feasibility classifiers and failure ontology codes weeks before binding assays finish.

---

## 2. The Three Telemetry Stages & Verification Invariants

### 2.1 Stage 1: Crude Synthesis LCMS (Day 10)
* **Measurements Ingested:** Crude HPLC purity %, synthesis yield (mg), and observed mass $[M+H]^+$.
* **Monoisotopic Mass Spec Verification:**
  Enforces exact mass tolerance:
  $$|M_{\text{observed}} - M_{\text{expected}}| \le 1.0\text{ Da} \quad \lor \quad \frac{|M_{\text{observed}} - M_{\text{expected}}|}{M_{\text{expected}}} < 500\text{ ppm}$$
* **Early Drop-Out Actions:**
  - If mass error $>1.0\text{ Da}$, candidate transitions immediately to `FAILED` with `SYN_WRONG_MASS` (detects deletion sequences or incomplete deprotection).
  - If crude purity $<40.0\%$, flags `SYN_CRUDE_PURITY_LOW`.
  - If yield $<1.0\text{ mg}$, flags `SYN_YIELD_LOW`.

### 2.2 Stage 2: Purified QC & Formulation / DLS (Day 18)
* **Measurements Ingested:** Purified HPLC purity %, PBS solubility ($\text{mg/mL}$), and Dynamic Light Scattering (DLS) polydispersity index (PDI).
* **Formulation Invariants:**
  - Purified HPLC purity $\ge 90.0\%$ (flags `SYN_PURITY_FAIL` if lower).
  - PBS solubility $\ge 0.5\text{ mg/mL}$ at pH 7.4 (flags `SOLUBILITY_LOW`).
  - DLS PDI $\le 0.30$ and aggregation index $\le 0.30$ (flags `AGGREGATION_HIGH`).

### 2.3 Stage 3: Bioassays & Surface Plasmon Resonance (Day 30)
* **Measurements Ingested:** Surface Plasmon Resonance (SPR) equilibrium dissociation constant ($K_d$ in $\text{nM}$), association rate ($k_{\text{on}}$ in $\text{M}^{-1}\text{s}^{-1}$), dissociation rate ($k_{\text{off}}$ in $\text{s}^{-1}$), and $\text{IC}_{50}$ ($\text{nM}$).
* **Potency Resolution & Fantasy Dissolution:**
  - Converts $K_d$ to normalized logarithmic potency score: $\text{p}K_d = -\log_{10}(K_d \cdot 10^{-9}) \times 10$.
  - Candidates with $K_d \le 10,000\text{ nM}$ ($10\,\mu\text{M}$) are marked `is_binder = True`, status $\to$ `evaluated`.
  - Non-binders ($K_d > 10,000\text{ nM}$ or censored above detection limit) are marked `is_binder = False`, status $\to$ `rejected` with `ASSAY_NON_BINDER`.
  - Dissolves Monte Carlo fantasy models into ground truth in the Research DAG.

---

## 3. Robust Tolerant Ingestion Engine

### 3.1 Flexible Column Alias Canonicalisation
The engine handles heterogeneous CSV/JSON drops from different CDMOs transparently by canonicalising headers:
- `Candidate_ID`, `sample_id`, `peptide_id` $\to$ `candidate_id`
- `Crude_Purity`, `purity_pct`, `Purity%` $\to$ `crude_purity_pct`
- `Observed_Mass`, `MW_obs`, `m_obs` $\to$ `mass_observed_da`
- `Solubility (mg/mL)`, `sol_mg_ml` $\to$ `solubility_mg_ml`
- `Kd (nM)`, `affinity_kd_nm` $\to$ `kd_nm`

---

## 4. Demonstrated Test Verification

In [`tests/test_telemetry_ingestion.py`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/tests/test_telemetry_ingestion.py):
* Verified mass tolerance match and failure tagging on mass mismatch.
* Verified batch CSV drop parsing for Stage 1 LCMS.
* Verified batch JSON drop parsing for Stage 2 Purified QC.
* Verified Stage 3 SPR binding kinetics ingestion, potency score calculation, and end-to-end state transitions across all 58 repository unit tests.
