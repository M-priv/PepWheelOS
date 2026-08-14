# Deep Implementation Plan: Pillar 1 — Epistemic Rigor, Domain DRC & Anti-Sycophancy

**Phase Alignment:** Phase 3 (Scientific Tooling, Epistemic Rigor & SRE Runtime)  
**Target Codebase Location:** `src/peptide_flywheel/contracts.py`, `src/peptide_flywheel/domain_drc.py`, `src/peptide_flywheel/dialectic.py`

---

## 1. Executive Summary & Problem Formulation

In LLM-driven peptide discovery, the most severe failure mode is the conflation of **syntactic fluency** (well-formed JSON conforming to Pydantic schemas) with **physical and biological truth** (thermodynamic stability, chemical synthesizability, stereochemical viability). Furthermore, when generative agents and red-team critique agents share the same model weights or prompting style, they suffer from **sycophantic convergence** and shared cognitive blind spots.

Pillar 1 establishes a **4-Tier Epistemic Firewall** inspired by aerospace (DO-178C / DO-333) and semiconductor design rule checking (DRC):
1. **Tier 1 (Syntactic Gate):** Schema validation, type checking, non-null assertions.
2. **Tier 2 (Logical Gate):** Formal Assume-Guarantee contract preconditions and DAG consistency.
3. **Tier 3 (Domain Biological DRC):** Hard physical and chemical invariant checks executed in deterministic Python *before* any model scoring.
4. **Tier 4 (Orthogonal 4-Paradigm Dialectic):** Adversarial Advocate vs. Sceptic agents adjudicated by an SMT/Rule Arbiter, where dissensus triggers wet-lab discriminative assays.

---

## 2. Mathematical & Algorithmic Specifications

### 2.1 Formal Assume-Guarantee Contracts $\mathcal{C} = (A, G)$
Every agent transformation $f: \mathcal{X} \to \mathcal{Y}$ is governed by a contract $\mathcal{C} = (A, G)$:
* **Assumptions ($A$):** Preconditions that the input context must satisfy:
  $$A(x) \iff \text{SequenceLength}(x) \in [4, 50] \land \text{Residues}(x) \subseteq \Sigma_{\text{IUPAC}} \land \text{TargetID}(x) \in \text{DAG}_{\text{Targets}}$$
* **Guarantees ($G$):** Postconditions guaranteed if and only if $A(x)$ holds:
  $$G(y) \iff \text{Parsed}(y) \land \forall r \in \text{RiskFlags}(y), r \in \text{Ontology}_{\text{Failures}} \land \text{UncertaintyRecorded}(y)$$

### 2.2 Biological Design Rule Checking (DRC) Invariant Formulations

The Domain DRC engine executes four categories of deterministic chemical checks:

#### A. SPPS Interchain $\beta$-Sheet Aggregation Invariant
Solid-Phase Peptide Synthesis (SPPS) fails on-resin when consecutive hydrophobic residues form intermolecular $\beta$-sheet fibrils that block the incoming activated Fmoc-amino acid.
$$\text{DRC}_{\text{hydrophobic}}(s) = \begin{cases} \text{FAIL}(\text{SYN\_HYDROPHOBIC\_SEQUENCE}) & \text{if } \exists \text{ substring } k \in s \text{ s.t. } |k| \ge 5 \land k \subseteq \{V, I, L, F, W, Y\} \\ \text{PASS} & \text{otherwise} \end{cases}$$

#### B. Base-Catalyzed Aspartimide Formation Invariant
Under piperidine Fmoc-deprotection (pH 12), `Asp-Gly` (`DG`), `Asp-Ser` (`DS`), and `Asp-Asn` (`DN`) motifs undergo rapid nucleophilic attack of the backbone amide on the $\beta$-carboxylic acid ester, forming a cyclic aspartimide intermediate that hydrolyzes into $\alpha/\beta$-isoaspartyl mixtures.
$$\text{DRC}_{\text{aspartimide}}(s) = \begin{cases} \text{FAIL}(\text{SYN\_MODIFICATION\_FAILED}) & \text{if } \text{RegexMatch}(s, \text{"D[GNS]"}) \\ \text{PASS} & \text{otherwise} \end{cases}$$

#### C. Isoelectric Point / Neutral Precipitation Invariant
Peptides with near-neutral net charge ($|z_{\text{pH } 7.4}| \le 0.5$) and high aliphatic index precipitate in neutral formulation buffers.
$$z(\text{pH}) = \sum_{i \in \{K, R, H, \text{N-term}\}} \frac{1}{1 + 10^{\text{pH} - \text{p}K_a(i)}} - \sum_{j \in \{D, E, C, Y, \text{C-term}\}} \frac{1}{1 + 10^{\text{p}K_a(j) - \text{pH}}}$$
If $|z(7.4)| < 0.5$ and GRAVY score $> 0.4$, trip `LOW_AQUEOUS_SOLUBILITY`.

#### D. Steric Coupling Invariant
Consecutive $\alpha,\alpha$-disubstituted residues (e.g., Aib-Aib) or consecutive $N$-methylated residues cause extreme steric hindrance, yielding $< 10\%$ crude SPPS coupling.

---

### 2.3 Adversarial Dialectic Committee & Dissensus Metric

```
                       [Candidate Card x + Target Dossier T]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     ┌────────────────────────┐                     ┌────────────────────────┐
     │  Advocate Agent (A)    │                     │  Sceptic Agent (S)     │
     │  Maximize Target Fit   │                     │  Falsify & Find Flaws  │
     └───────────┬────────────┘                     └───────────┬────────────┘
                 │ (Score s_A, Claims C_A)                      │ (Score s_S, Liabilities L_S)
                 └───────────────────────┬──────────────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │   SMT / Rule Arbiter          │
                         │   Adjudicate Claims & Checks  │
                         └───────────────┬───────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                 [Δ_dissensus ≤ 0.35]             [Δ_dissensus > 0.35]
                         │                               │
                         ▼                               ▼
               [Standard Decision]             [Route to Discriminative]
               (Advance / Reject)              [Active-Learning Assay  ]
```

* **Advocate Output:** $s_A \in [0, 1]$ (affinity expectation), evidence claims $\mathcal{C}_A$.
* **Sceptic Output:** $s_S \in [0, 1]$ (liability penalty), failure modes $\mathcal{L}_S$.
* **Dissensus Delta:**
  $$\Delta_{\text{dissensus}} = |s_A - (1 - s_S)| + \lambda \cdot \text{UncertaintySpread}(A, S)$$
* **Gating Policy:**
  * If $\Delta_{\text{dissensus}} > 0.35$: Mark as *High Epistemic Dissensus* $\to$ route to wet-lab discriminative assay in Phase 4.
  * If $\Delta_{\text{dissensus}} \le 0.35$ and $s_A \ge 0.80 \land s_S \le 0.20$: Mark as *Consensus Pass*.
  * If $s_S > 0.60$: Mark as *Consensus Reject* $\to$ log failure memory.

---

## 3. Data Structures & Schemas

```python
# src/peptide_flywheel/contracts.py
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum

class ContractSeverity(str, Enum):
    FATAL = "fatal"
    WARNING = "warning"
    INFORMATIONAL = "informational"

@dataclass
class DRCRuleResult:
    rule_id: str
    passed: bool
    severity: ContractSeverity
    failure_code: str | None = None
    message: str = ""
    culprit_subsequence: str | None = None
    positions: list[int] = field(default_factory=list)

@dataclass
class DialecticVerdict:
    candidate_id: str
    advocate_score: float
    sceptic_score: float
    dissensus_delta: float
    arbiter_decision: str  # "PASS", "REJECT", "DISCRIMINATIVE_ASSAY"
    identified_liabilities: list[str]
    falsification_experiments: list[str]
```

---

## 4. Implementation Steps & Milestones

1. **`src/peptide_flywheel/contracts.py`**:
   - Implement `@enforce_contract` decorator verifying input assumptions and output invariants.
   - Implement pipeline precondition guards for target and candidate artifacts.
2. **`src/peptide_flywheel/domain_drc.py`**:
   - Implement `check_hydrophobic_runs()` with sequence position tracking.
   - Implement `check_aspartimide_motifs()` with `D[GNS]` regex scanner.
   - Implement `check_isoelectric_precipitation()` using Henderson-Hasselbalch pKa table.
   - Implement `run_biological_drc_suite(sequence: str) -> list[DRCRuleResult]`.
3. **`src/peptide_flywheel/dialectic.py`**:
   - Implement `AdvocateAgentRunner` with prompt targeting binding mode and interface fit.
   - Implement `ScepticAgentRunner` with inverted utility prompt targeting synthesis/assay failure.
   - Implement `SMTArbiter` computing $\Delta_{\text{dissensus}}$ and assigning routing tags.
4. **Integration & CLI Hooks**:
   - Integrate DRC preflight checks into `run_manual_flywheel_round.py` and `build_prompt_batch.py`.

---

## 5. Verification & Test Suite

- `tests/test_domain_drc.py`:
  - Test 1: Validate sequence `"ACDEFVVVVVGHIKL"` fails with `SYN_HYDROPHOBIC_SEQUENCE` at positions 5–9.
  - Test 2: Validate sequence `"WNDGSFK"` fails with `SYN_MODIFICATION_FAILED` (aspartimide liability at `DG`).
  - Test 3: Validate balanced peptide `"KWKLFKKIEKWLFLG"` passes DRC cleanly.
- `tests/test_dialectic.py`:
  - Test 1: Verify that high advocate score (0.9) vs. high sceptic liability (0.8) yields $\Delta_{\text{dissensus}} = 0.70$ and triggers `DISCRIMINATIVE_ASSAY`.
  - Test 2: Verify consensus pass routes candidate to synthesis queue.
