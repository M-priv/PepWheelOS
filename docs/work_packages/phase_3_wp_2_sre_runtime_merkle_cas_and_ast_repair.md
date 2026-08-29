# Phase 3 — Work Package 2: SRE Runtime, Merkle CAS & AST Repair (Pillar 4)

**Module Location:** `src/peptide_flywheel/cas_store.py`, `src/peptide_flywheel/ast_repair.py`, `src/peptide_flywheel/circuit_breaker.py`, `src/peptide_flywheel/prompt_pipeline.py`  
**Test Suites:** `tests/test_cas_store.py`, `tests/test_ast_repair.py`, `tests/test_circuit_breaker.py`  
**Language Standard:** UK English  

---

## 1. Executive Summary & First-Principles Problem

In naive multi-agent LLM systems:
1. Every agent passes the full target dossier, hypothesis, and candidate history in every prompt. For 50 candidates, this wastes 85%+ of tokens on repeated static text.
2. Dynamic timestamps at the top of prompts invalidate GPU Key-Value (KV) caches on LLM inference servers.
3. Minor formatting flaws (e.g. LLM outputting `"0.85"` instead of `0.85`, adding whitespace `" kwk "`, or omitting `candidate_id`) trigger expensive 3-step retry storms ($3\times$ latency and cost).
4. Remote API rate limits or network timeouts crash entire batch discovery runs.

---

## 2. Mathematical & Architectural Mechanisms

### 2.1 Content-Addressed Storage (`cas_store.py`)
* Serialises entities deterministically and indexes them by their SHA-256 hash (`cas://<sha256>`).
* Agents pass lightweight `CompactContextEnvelope` pointers (`target_ref: "cas://..."`) rather than copying megabytes of JSON.
* Implements **RFC 6902 JSON Patch deltas** (`[{"op": "add", "path": "/risk_flags/-", "value": "..."}]`) for micro-state transitions.

### 2.2 3-Tier Prefix-Invariant Prompts (`prompt_pipeline.py`)
* `Tier 1 (Static System)`: Permanent persona, output schema, and ontology (100% KV-cached across all runs).
* `Tier 2 (Campaign Context)`: Target biology and controls (cached across campaign).
* `Tier 3 (Dynamic Tail)`: Specific candidate sequence and task instruction.
* Yields **40–80% lower inference latency** and token costs on modern providers.

### 2.3 3-State SRE Circuit Breaker (`circuit_breaker.py`)
* State machine: `CLOSED` (normal) $\to$ `OPEN` (tripped when failure rate $>40\%$) $\to$ `HALF_OPEN` (probing).
* If remote LLM APIs suffer outages, the circuit trips immediately to local heuristic scoring ([`scoring.py`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/scoring.py)), allowing campaigns to proceed without crashing.
* Failed payloads are logged to disk in `.flywheel_dlq/` (Dead-Letter Queue) for post-mortem analysis.

---

## 3. Deep Dive: Zero-LLM Deterministic AST Repair & Score Clamping (`ast_repair.py`)

### 3.1 Two-Stage Repair Hierarchy
1. **Stage 1 (Zero-LLM Normalisation in $<0.1\text{ ms}$):**
   - Automatically repairs string-to-float coercions (`"0.85"` $\to$ `0.85`).
   - Strips whitespace and uppercases IUPAC sequence letters (`" kwk "` $\to$ `"KWK"`).
   - Auto-injects expected context IDs (`target_id`, `hypothesis_id`, `candidate_id`).
   - Converts comma strings to arrays (`"A, B"` $\to$ `["A", "B"]`).
2. **Stage 2 (Subtree Isolation & 50-Token Micro-Repair):**
   - If a structural schema error persists, `isolate_invalid_ast_subfields()` pinpoints *only* the failing subfield (e.g. `modality`), sending a 50-token micro-prompt rather than regenerating an entire 800-token candidate card.

### 3.2 Risks & Mitigants of Deterministic Score Clamping

| Risk | What Could Go Wrong | Code Mitigant in Codebase |
|---|---|---|
| **1. Scale Ambiguity ($0\text{--}1$ vs $0\text{--}100$)** | An LLM outputs `85.0` (meaning 85%). If blindly clamped to `1.0`, a 100-point scale interprets this as 1% (terrible), or a 1-point scale interprets it as 100% (artificially perfect). | [`ast_repair.py:L78-82`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/ast_repair.py#L78-L82): Detects when a probability/confidence field is in $(1.0, 100.0]$ and divides by $100.0$ (`85.0` $\to$ `0.85`) rather than blunt chopping. |
| **2. Silent Masking of Severe Hallucinations** | An LLM outputs `-500.0` or `14,000.0` because the prompt broke. Silently clamping to `0.0` or `1.0` conceals a catastrophic prompt defect as a normal prediction. | [`ast_repair.py:L70-73`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/ast_repair.py#L70-L73): Detects extreme values outside $[-10.0, 150.0]$ and logs an explicit `WARNING` in `repairs_applied` and the evaluation report. |
| **3. Negative Ranking Loss (Zero Floor Saturation)** | Candidate A is slightly unmanufacturable (`-0.1`), while Candidate B is a complete disaster (`-50.0`). Clamping both to `0.0` destroys relative failure gradients. | **Pillar 3 Decoupled Hurdle Modeling** ([`docs/planning/pillar_3_negative_data_and_hurdle_modeling.md`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/planning/pillar_3_negative_data_and_hurdle_modeling.md)): Separates the binary Feasibility Classifier from the Potency Regressor, categorising failures with discrete ontology codes in [`docs/04_failure_ontology.md`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/docs/04_failure_ontology.md) rather than uncalibrated negative numbers. |
| **4. Physical / Thermodynamic Unit Confusion** | In biophysics, negative free energy ($\Delta G = -11.2\,\text{kcal/mol}$) indicates extremely tight binding. Clamping `-11.2` to `0.0` would destroy the best drug candidate. | [`ast_repair.py:L49-56`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/ast_repair.py#L49-L56): Clamping is restricted strictly to an explicit whitelist of normalised score fields (`manufacturability_score`, `overall_score`, `confidence`), and is **never** applied to thermodynamic energies ($\Delta G$), dissociation constants ($K_d$), or $\text{IC}_{50}$ concentrations. |
