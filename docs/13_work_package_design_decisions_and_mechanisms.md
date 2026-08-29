# Work Package Design Decisions, Mechanisms & First-Principles Rationale

**Document ID:** `DOC-ARCH-013`  
**Status:** Approved Reference Standard  
**Language Standard:** UK English  
**Scope:** In-depth architectural, mathematical, and biophysical rationale for all completed work packages (Phase 3 & Phase 4).

---

## 1. Phase 3 — Work Package 1: Epistemic Rigour & Domain DRC (Pillar 1)

### Files Built:
* `src/peptide_flywheel/contracts.py`
* `src/peptide_flywheel/domain_drc.py`
* `src/peptide_flywheel/dialectic.py`
* `tests/test_domain_drc.py`, `tests/test_dialectic.py`

### 1.1 The Core Problem: Why Pydantic / Schema Validation Fails in Physical Science
In software engineering, schema validation (e.g. JSON schema, Pydantic) confirms that a payload is **syntactically well-formed** (e.g., `sequence` is a string, `score` is a float).  
However, in physical drug discovery, **an output can be 100% syntactically valid yet physically impossible, toxic, or unmanufacturable**. For example:
- A sequence containing `DG` (Asp-Gly) is a valid string, but undergoes base-catalysed aspartimide cyclisation in solid-phase peptide synthesis (SPPS), destroying yield.
- A sequence containing `VVVLL` is valid text, but forms irreversible $\beta$-sheet amyloid fibrils that clog synthesis resin and precipitate during purification.

### 1.2 The Solution & Mechanism:
1. **Assume-Guarantee Formal Contracts (`@enforce_contract` in `contracts.py`):**
   - Implements the aerospace/EDA formal methods pattern. Every agent tool and transformation declares pre-conditions (*Assumptions*) and post-conditions (*Guarantees*). If an agent hallucinates a sequence shorter than 2 residues or returns NaN scores, the contract aborts before spending resources.
2. **Biological Design Rule Checking (DRC) (`domain_drc.py`):**
   - Modelled after semiconductor VLSI design rule checks. Runs deterministic physical invariant scans:
     - `DRC-001 (Aspartimide)`: Detects `D[GNS]` motifs and flags base-catalysed succinimide ring formation.
     - `DRC-002 (Poly-Hydrophobic Collapse)`: Detects $\ge 5$ consecutive aliphatic/aromatic residues (`[VILFYW]{5,}`) prone to on-resin aggregation.
     - `DRC-003 (Isoelectric Precipitation)`: Solves Henderson-Hasselbalch charge equilibrium; flags neutral peptides ($|\text{charge}| < 0.5$ at pH 7.4) with hydropathy $>0.0$ that precipitate in physiological formulation.
     - `DRC-004 (Unpaired Cysteine Oxidation)`: Flags odd numbers of cysteines that form scrambled intermolecular disulphides.
     - `DRC-005 (Steric Poly-Proline Clashes)`: Detects $[P]{3+}$ rigid conformational locks.
3. **Adversarial Dialectic Committee (`dialectic.py`):**
   - LLMs suffer from **sycophancy and optimistic bias** (generating rationale that justifies their own designs).
   - We deploy an **Advocate Agent** (searching for positive binding mechanisms) pitted against an independent **Sceptic Agent** (tasked exclusively with uncovering failure modes and manufacturing liabilities).
   - An SMT/Rule Arbiter computes the dissensus metric:
     $$\Delta_{\text{dissensus}} = |\text{Score}_{\text{advocate}} - \text{Score}_{\text{sceptic}}|$$
   - When $\Delta_{\text{dissensus}} > 0.35$, the candidate is automatically flagged as high-epistemic-uncertainty and routed to targeted assay design rather than unhedged scale-up.

---

## 2. Phase 3 — Work Package 2: SRE Runtime, Merkle CAS & AST Repair (Pillar 4)

### Files Built:
* `src/peptide_flywheel/cas_store.py`
* `src/peptide_flywheel/ast_repair.py`
* `src/peptide_flywheel/circuit_breaker.py`
* `src/peptide_flywheel/prompt_pipeline.py`
* `tests/test_cas_store.py`, `tests/test_ast_repair.py`, `tests/test_circuit_breaker.py`

### 2.1 The Core Problem: Multi-Agent Context Bloat & Retry Storms
In naive multi-agent systems:
1. Every agent passes the full target dossier, hypothesis, and candidate history in every prompt. For 50 candidates, this wastes 85%+ of tokens on repeated static text.
2. Dynamic timestamps at the top of prompts invalidate GPU Key-Value (KV) caches on LLM inference servers.
3. Minor formatting flaws (e.g. LLM outputting `"0.85"` instead of `0.85`, adding whitespace `" kwk "`, or omitting `candidate_id`) trigger expensive 3-step retry storms ($3\times$ latency and cost).
4. Remote API rate limits or network timeouts crash entire batch discovery runs.

### 2.2 The Solution & Mechanism:
1. **Content-Addressed Storage (`cas_store.py`):**
   - Serialises entities deterministically and indexes them by their SHA-256 hash (`cas://<sha256>`).
   - Agents pass lightweight `CompactContextEnvelope` pointers (`target_ref: "cas://..."`) rather than copying megabytes of JSON.
   - Implements **RFC 6902 JSON Patch deltas** (`[{"op": "add", "path": "/risk_flags/-", "value": "..."}]`) for micro-state transitions.
2. **Zero-LLM Deterministic AST Repair (`ast_repair.py`):**
   - Automatically repairs string-to-float coercions, clamps bounded scores to $[0, 1]$, uppercases IUPAC sequence letters, and auto-injects expected context IDs without invoking another LLM call.
   - If a structural schema error persists, it isolates *only* the failing subfield so a 50-token micro-repair can be run instead of re-generating an entire 800-token candidate card.
3. **3-State SRE Circuit Breaker (`circuit_breaker.py`):**
   - State machine: `CLOSED` (normal) $\to$ `OPEN` (tripped when failure rate $>40\%$) $\to$ `HALF_OPEN` (probing).
   - If remote LLM APIs suffer outages, the circuit trips immediately to local heuristic scoring ([`scoring.py`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/scoring.py)), allowing campaigns to proceed without crashing.
   - Failed payloads are logged to disk in `.flywheel_dlq/` (Dead-Letter Queue) for post-mortem analysis.
4. **3-Tier Prefix-Invariant Prompts (`prompt_pipeline.py`):**
   - `Tier 1 (Static System)`: Permanent persona, output schema, and ontology (100% KV-cached across all runs).
   - `Tier 2 (Campaign Context)`: Target biology and controls (cached across campaign).
   - `Tier 3 (Dynamic Tail)`: Specific candidate sequence and task instruction.
   - Yields 40–80% lower inference latency and token costs on modern providers.

### 2.3 Deep Dive: The Mechanics, Risks & Mitigants of Deterministic Score Clamping

#### What Clamping to $[0.0, 1.0]$ Means:
Forcing a continuous numerical output to remain strictly bounded within a defined minimum floor ($0.0$) and maximum ceiling ($1.0$). If an output is negative (e.g. `-0.05`), it is pulled to `0.0`; if an output is $>1.0$, it is capped at `1.0`; if within range (e.g. `0.85`), it is left unchanged.

#### Potential Risks & Architectural Mitigants:

| Risk | What Could Go Wrong | Code Mitigant in Codebase |
|---|---|---|
| **1. Scale Ambiguity ($0\text{--}1$ vs $0\text{--}100$)** | An LLM outputs `85.0` (meaning 85%). If blindly clamped to `1.0`, a 100-point scale interprets this as 1% (terrible), or a 1-point scale interprets it as 100% (artificially perfect). | [`ast_repair.py:L78-82`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/ast_repair.py#L78-L82): Detects when a probability/confidence field is in $(1.0, 100.0]$ and divides by $100.0$ (`85.0` $\to$ `0.85`) rather than blunt chopping. |
| **2. Silent Masking of Severe Hallucinations** | An LLM outputs `-500.0` or `14,000.0` because the prompt broke. Silently clamping to `0.0` or `1.0` conceals a catastrophic prompt defect as a normal prediction. | [`ast_repair.py:L70-73`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/ast_repair.py#L70-L73): Detects extreme values outside $[-10.0, 150.0]$ and logs an explicit `WARNING` in `repairs_applied` and the evaluation report. |
| **3. Negative Ranking Loss (Zero Floor Saturation)** | Candidate A is slightly unmanufacturable (`-0.1`), while Candidate B is a complete disaster (`-50.0`). Clamping both to `0.0` destroys relative failure gradients. | **Pillar 3 Decoupled Hurdle Modeling** ([`docs/planning/pillar_3_negative_data_and_hurdle_modeling.md`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/planning/pillar_3_negative_data_and_hurdle_modeling.md)): Separates the binary Feasibility Classifier from the Potency Regressor, categorising failures with discrete ontology codes in [`docs/04_failure_ontology.md`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/04_failure_ontology.md) rather than uncalibrated negative numbers. |
| **4. Physical / Thermodynamic Unit Confusion** | In biophysics, negative free energy ($\Delta G = -11.2\,\text{kcal/mol}$) indicates extremely tight binding. Clamping `-11.2` to `0.0` would destroy the best drug candidate. | [`ast_repair.py:L49-56`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/ast_repair.py#L49-L56): Clamping is restricted strictly to an explicit whitelist of normalised score fields (`manufacturability_score`, `overall_score`, `confidence`), and is **never** applied to thermodynamic energies ($\Delta G$), dissociation constants ($K_d$), or $\text{IC}_{50}$ concentrations. |

---


## 3. Phase 3 — Work Package 3: Multi-Objective Pareto Sorting & Conformal Prediction (Pillars 3 & 5A)

### Files Built:
* `src/peptide_flywheel/pareto_sort.py`
* `src/peptide_flywheel/conformal.py`
* `tests/test_pareto_conformal.py`

### 3.1 The Core Problem: The 1D Scalar Trap & Uncalibrated AI Models
- **The Scalar Trap:** Combining Potency, Synthesisability, Solubility, and Toxicity into a single weighted sum (e.g. $\text{Score} = 0.5 \cdot \text{Potency} + 0.5 \cdot \text{Solubility}$) creates "cheater molecules": a peptide with 10/10 potency but 0/10 solubility gets a "5/10" and looks identical to an average peptide.
- **Uncalibrated Confidence:** Deep learning models and LLMs frequently output 95% confidence on out-of-distribution candidates that fail in the lab.

### 3.2 The Solution & Mechanism:
1. **NSGA-II Non-Dominated Pareto Sorting (`pareto_sort.py`):**
   - Partitions candidates into non-dominated Pareto fronts ($\mathcal{F}_1, \mathcal{F}_2, \dots$).
   - A candidate $p$ belongs to Front 1 if *no other candidate is strictly better across all objectives*.
   - Uses **Crowding Distance** along the front to preserve diversity and prevent selecting 20 identical trade-offs.
2. **Split Conformal Prediction Intervals (`conformal.py`):**
   - Calibrates empirical non-conformity residuals on historical validation runs.
   - Generates confidence intervals $[\hat{\mu} - \hat{q}, \hat{\mu} + \hat{q}]$ with **guaranteed 90% statistical coverage** without assuming Gaussian error distributions.
   - Automatically flags high-uncertainty candidates (width $> 0.35$) for active learning prioritisation.

---

## 4. Phase 3 — Work Package 4: CLI Integration, Workflows & Ponytail Refactor

### Files Built / Modified:
* `src/peptide_flywheel/workflows.py`
* `scripts/validate_agent_output.py`
* `docs/12_language_and_performance_architecture.md`

### 4.1 The Core Rationale:
- **Two-Language Symbiosis:** Established the architectural standard where Python controls the agent graph, contracts, and ML interfaces, while CPU-intensive routines (like massive combinatorial DRC screening) are isolated for future Rust extensions (via PyO3/Maturin) only when scale warrants it ($>100,000$ sequences).
- **In-Workflow DRC:** Integrated the biological DRC suite directly into `run_manual_flywheel_round()`, ensuring that every candidate card generated in the Research DAG contains exact Henderson-Hasselbalch net charge, Kyte-Doolittle hydropathy, and hard DRC stop codes.
- **Ponytail Refactoring:** Audited and trimmed dead variables, unused imports, and manual slice loops using Python standard library idioms (`collections.deque`, `Counter`), keeping the core lean and fast.

---

## 5. Phase 4 — Work Package 1: Determinantal Point Process (DPP) Batch Diversity (Pillar 2A)

### Files Built:
* `src/peptide_flywheel/dpp_sampler.py`
* `tests/test_dpp_sampler.py`

### 5.1 The Core Problem: Catastrophic Batch Redundancy
When selecting a batch of $q=10$ to $q=100$ candidates for wet-lab synthesis, standard top-$K$ greedy selection picks 10 near-identical single-point mutants of the top lead (e.g. `KWKLFKKIEKWLFLG`, `KWKLFKKIEKWLFLA`, `KWKLFKKIEKWLFLV`).  
If that scaffold has an unforeseen synthesis failure or unmodelled binding liability, the **entire 3-week synthesis budget is lost with zero information gain**.

### 5.2 The Solution & Mechanism:
1. **$L$-Ensemble Formulation:**
   We construct a symmetric positive semi-definite matrix:
   $$L_{ij} = q(x_i) \cdot K_{ij} \cdot q(x_j)$$
   - **Quality Factor ($q(x_i)$):** $q_i = \exp\left(\frac{\text{Score}(x_i)}{\tau}\right)$ scaled by temperature $\tau > 0$.
   - **Diversity Similarity ($K_{ij}$):** $K_{ij} = \exp(-\gamma \|\mathbf{e}_i - \mathbf{e}_j\|^2)$ computed over sequence embeddings.
2. **Greedy Submodular MAP Selection:**
   The probability of selecting subset $Y$ of size $q$ is proportional to the volume of the parallelotope spanned by their feature vectors: $\mathcal{P}(Y) \propto \det(L_Y)$.
   - We iteratively add candidate $i^* = \arg\max_{i \notin Y} \log \det(L_{Y \cup \{i\}})$ in $\mathcal{O}(q^2 N)$ time.
   - If two candidates are structurally similar ($K_{ij} \to 1$), the determinant $\det(L_Y)$ collapses toward zero (geometric repulsion).
3. **Built-in 24-Dimensional Sequence Feature Extractor:**
   - 20 amino acid composition frequencies + length + Kyte-Doolittle GRAVY + Henderson-Hasselbalch net charge at pH 7.4 + aromatic fraction.
   - Operates as a fast, zero-dependency embedding generator when neural transformer embeddings (ESM-2) are absent.
4. **Demonstrated Impact:**
   - In automated testing on clustered candidate pools, DPP preserved the top lead from Cluster 1 while selecting diverse leads from Cluster 2, achieving **$>2\times$ higher average pairwise distance** than naive top-$K$ selection.

---

## 6. Phase 4 — Work Package 2: Asynchronous Bayesian Optimisation & Monte Carlo Fantasies (Pillar 2B)

### 6.1 The Core Problem: The Physical Latency Mismatch
In peptide drug discovery, physical synthesis and wet-lab assays require 2 to 6 weeks per round, whilst computational generation takes seconds. Sequential optimisation ($q=1$) leaves the synthesis team sitting idle for a month.  
However, designing Round $N+1$ without Round $N$'s results causes standard optimisers to propose near-duplicate clones of in-flight candidates, wasting budget on redundant assays.

---

### 6.2 Mathematical Foundation & Key Mechanics

#### 1. Why the Mean Depends on Lab Outcomes, but Variance Does Not:
In Gaussian Process conditioning over measured data $\mathbf{y}$ and new point $x^*$:
* **Conditional Mean:** $\mu(x^*) = \mathbf{k}_*^T (\mathbf{K} + \sigma_n^2 \mathbf{I})^{-1} \mathbf{y}$  
  *(Contains $\mathbf{y}$ at the end: the expected height is a linear combination of physical lab measurements).*
* **Conditional Variance:** $\sigma^2(x^*) = k(x^*, x^*) - \mathbf{k}_*^T (\mathbf{K} + \sigma_n^2 \mathbf{I})^{-1} \mathbf{k}_*$  
  *(Contains **NO** $\mathbf{y}$: uncertainty depends solely on coordinate locations $X$ and kernel distance).*

**The Flashlight Analogy:** Turning on a flashlight at location $X$ illuminates that spot (uncertainty $\sigma \to 0$) regardless of whether the light reveals treasure ($y=100$) or an empty floor ($y=0$). We can compute the future uncertainty collapse for in-flight candidates $X_{\text{pending}}$ weeks before physical assays finish.

---

### 6.3 Monte Carlo Fantasy Worlds: Hedging vs. "Shooting Blind"

Since the mean $\mu(x)$ depends on unknown experimental potency, we sample $M=32$ correlated hypothetical outcomes from the joint GP posterior:
$$\tilde{\mathbf{y}}^{(m)} \sim \mathcal{N}\left(\boldsymbol{\mu}_{\text{pending}}, \mathbf{\Sigma}_{\text{pending}}\right)$$

#### How the 32 Fantasy Worlds Protect the Campaign:
* **In worlds where Round $N$ is a WINNER ($\tilde{y}=9.5$):** The model focuses on fine-tuning mutations and capping modifications around the lead.
* **In worlds where Round $N$ is a DUD ($\tilde{y}=0.1$):** The model eliminates that chemical island and pivots to the second-best orthogonal scaffold.
* **The Asynchronous Portfolio ($\alpha_{\text{async}} = \frac{1}{M}\sum \alpha^{(m)}$):** Round $N+1$ constructs an optimal 50/50 hedge:
  - 50% follow-up bets on winning mutations.
  - 50% insurance bets on backup scaffolds (already in the synthesiser 3 weeks early if Round $N$ fails).

---

### 6.4 The 4 Physical Anchors Governing the Fantasies

The fantasy draws are not arbitrary hallucinations; they are strictly bound by:
1. **Historical Physical Ground Truth ($\mathcal{D}_{\text{measured}}$):** Anchors the prior and baseline covariance.
2. **ESM-2 Protein Physics & Kernel Geometry ($k(x, x')$):** Smoothness and homology prevent physically impossible jumps.
3. **Staggered Physical Telemetry (Day 10/18 Ingestion):** Day 10 crude LCMS purity and Day 18 DLS solubility inject real physical data weeks before the 30-day bioassay.
4. **Deterministic Biological DRC Invariants:** `DRC-001` to `DRC-005` enforce hard chemical stops regardless of fantasy draws.

**The Epistemic Tightening Curve:**  
* **Round 1 (Cold Start):** Broad, diffuse fantasies $\to$ spreads wide bets across 3+ distinct scaffold families.
* **Round 2 (Calibrated):** Fitted to real assay noise floor $\to$ 50/50 hedge between lead family and backup scaffold.
* **Round 3+ (Refinement):** Narrow, highly focused fantasies $\to$ high-precision lead optimisation.

---

### 6.5 Automated Telemetry Calibration & Scientist Review

When real wet-lab CSV/JSON data arrives:
1. **Automated MML Refitting (< 50ms):** The GP automatically updates length-scale $\ell$, signal amplitude $\sigma_f^2$, and assay noise $\sigma_n^2$ via Maximum Marginal Likelihood:
   $$\log p(\mathbf{y} \mid X, \boldsymbol{\theta}) = -\frac{1}{2} \mathbf{y}^T \mathbf{K}_{\boldsymbol{\theta}}^{-1} \mathbf{y} - \frac{1}{2} \log |\mathbf{K}_{\boldsymbol{\theta}}| - \frac{N}{2} \log(2\pi)$$
2. **Fantasy Dissolution:** The $M=32$ fantasy worlds are automatically deleted and collapse into the single, true empirical reality.
3. **Review-by-Exception:** Human scientists only intervene if an SRE anomaly is detected (e.g. assay noise $\sigma_n^2$ spikes $>3\times$ due to plate contamination or 0% batch synthesis yield).

