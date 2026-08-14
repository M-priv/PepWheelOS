# Deep Implementation Plan: Pillar 2 — Asynchronous Pipelining & Multi-Fidelity Batch BO

**Phase Alignment:** Phase 4 (Experimental Feedback, Negative Data & Asynchronous Loop)  
**Target Codebase Location:** `src/peptide_flywheel/dpp_sampler.py`, `src/peptide_flywheel/async_bo.py`, `src/peptide_flywheel/telemetry_ingestion.py`

---

## 1. Executive Summary & Problem Formulation

In peptide drug discovery, the cycle time is governed by physical synthesis and wet-lab assays (2–6 weeks per round), whereas computational candidate generation takes seconds. Standard sequential optimization ($q=1$ Bayesian optimization) is economically and operationally non-viable.

Pillar 2 solves two critical operational constraints:
1. **Batch Information Gain Maximization ($q \in [10, 1000]$):** Eliminates candidate redundancy by enforcing mathematical sequence diversity via **Determinantal Point Processes (DPP)** over ESM-2 embeddings.
2. **Asynchronous Overlapping Pipelining:** Enables continuous lab utilization by designing Round $N+1$ while Round $N$ is in-flight at the CRO/CDMO, using **Monte Carlo Fantasy Rollouts** over pending points ($X_{\text{pending}}$) and **Staggered Multi-Stage Telemetry Ingestion** (Day 10 Crude LCMS $\to$ Day 18 QC $\to$ Day 30 Bioassay).

---

## 2. Mathematical & Algorithmic Specifications

### 2.1 Determinantal Point Process (DPP) Sequence Repulsion

To select a diverse batch of $q$ candidates from a large library $\mathcal{X}$ ($|\mathcal{X}| \gg q$), we define an $L$-ensemble kernel:
$$L_{ij} = q(x_i) \cdot K_{ij} \cdot q(x_j)$$
* $q(x_i) = \exp(\text{Score}(x_i) / \tau)$: Quality score derived from multi-objective Pareto ranking and manufacturability.
* $K_{ij} = \exp(-\gamma \|\mathbf{e}_i - \mathbf{e}_j\|^2)$: Structural diversity similarity computed from ESM-2 sequence embeddings $\mathbf{e}_i, \mathbf{e}_j \in \mathbb{R}^{1280}$.

The probability of selecting batch $Y \subseteq \mathcal{X}$ with $|Y| = q$ is:
$$\mathcal{P}(Y) = \frac{\det(L_Y)}{\sum_{|Y'|=q} \det(L_{Y'})}$$

**Greedy $k$-DPP Maximum A Posteriori (MAP) Selection Algorithm:**
```python
def select_dpp_batch(candidates: list[dict], q: int, quality_scores: list[float], embeddings: np.ndarray) -> list[dict]:
    # 1. Construct L-ensemble
    K = rbf_kernel(embeddings)
    L = np.diag(quality_scores) @ K @ np.diag(quality_scores)
    
    # 2. Greedy submodular selection maximizing log det(L_Y)
    selected_indices = []
    for _ in range(q):
        best_gain = -np.inf
        best_idx = None
        for i in range(len(candidates)):
            if i in selected_indices:
                continue
            cand_set = selected_indices + [i]
            gain = np.linalg.slogdet(L[np.ix_(cand_set, cand_set)])[1]
            if gain > best_gain:
                best_gain = gain
                best_idx = i
        selected_indices.append(best_idx)
    return [candidates[i] for i in selected_indices]
```

---

### 2.2 Asynchronous Bayesian Optimization with Monte Carlo Fantasy Rollouts

When generating Round $N+1$, candidates $X_{\text{pending}}^{(N)} = \{x_1^{(N)}, \dots, x_q^{(N)}\}$ are in-flight in the wet-lab with unknown outcomes.

```
  Historical Data D_N
          │
          ├──► Joint Posterior GP: p(y_pending | X_pending, D_N)
          │            │
          │            ▼ Sample M=32 Fantasy Draws
          │     { y_tilde^(1), ..., y_tilde^(M) }
          │            │
          ▼            ▼
  Condition M Augmented GP Models: M^(m) = GP( D_N ∪ { (X_pending, y_tilde^(m)) } )
                       │
                       ▼
  Asynchronous Acquisition: α_async(x) = (1/M) * Σ α(x | M^(m))
```

**Mathematical Variance Reduction:**
The posterior covariance conditioned on $X_{\text{pending}}$ is:
$$\mathbf{\Sigma}_{\text{post}}(x^*) = k(x^*, x^*) - \mathbf{k}(x^*, [X_N, X_{\text{pending}}]) \mathbf{K}^{-1} \mathbf{k}([X_N, X_{\text{pending}}], x^*)$$
Because uncertainty $\sigma^2(x)$ collapses near $X_{\text{pending}}$, the acquisition engine is mathematically repelled from proposing duplicate or redundant variants of Round $N$, naturally exploring complementary chemical space or hedging leads.

---

### 2.3 Staggered Multi-Stage Telemetry Ingestion Timeline

```
Day 0           Day 10 (Stage 1)       Day 18 (Stage 2)        Day 30 (Stage 3)
  │                    │                      │                       │
  ▼                    ▼                      ▼                       ▼
Order Sent       Crude LCMS QC          Purified Solubility      SPR / Bioassays
to CRO CDMO     (Yield & Purity)        (Aggregation / DLS)      (K_d / IC50 Kinetics)
                Update Feasibility      Update Formulation       Resolve Fantasy GP
                GP Weeks Early!         Liability Models         to Exact Ground Truth
```

---

## 3. Data Structures & Schemas

```python
# src/peptide_flywheel/models.py additions
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any

class CandidateLifecycleState(str, Enum):
    DESIGNED = "designed"
    PENDING_SYNTHESIS = "pending_synthesis"
    PENDING_QC = "pending_qc"
    PENDING_BIOASSAY = "pending_bioassay"
    VALIDATED_ACTIVE = "validated_active"
    VALIDATED_INACTIVE = "validated_inactive"
    SYNTHESIS_FAILED = "synthesis_failed"
    QUALITY_FAILED = "quality_failed"

class PendingEvaluationRecord(BaseModel):
    candidate_id: str
    campaign_id: str
    round_index: int
    lifecycle_state: CandidateLifecycleState
    committed_at: datetime
    expected_completion_date: datetime
    interim_telemetry: dict[str, Any] = Field(default_factory=dict)
```

---

## 4. Implementation Steps & Milestones

1. **`src/peptide_flywheel/dpp_sampler.py`**:
   - Implement ESM-2 embedding extraction or sequence descriptor distance matrix.
   - Implement greedy submodular $k$-DPP MAP batch selection.
   - Add diversity index telemetry reporting.
2. **`src/peptide_flywheel/async_bo.py`**:
   - Implement `PendingCandidateRegistry` tracking in-flight candidates in DAG.
   - Implement Monte Carlo fantasy sampling ($M=32$ draws).
   - Implement pending-aware acquisition function wrapper.
3. **`src/peptide_flywheel/telemetry_ingestion.py`**:
   - Implement stage-1 (Crude LCMS) parser for interim yield/purity updates.
   - Implement stage-2 (QC formulation) parser.
   - Connect telemetry updates to state transitions (`PENDING_SYNTHESIS` $\to$ `PENDING_QC` $\to$ `PENDING_BIOASSAY`).
4. **Integration**:
   - Update `run_manual_flywheel_round.py` and `active_learning.py` to support `--pending-records` parameter.

---

## 5. Verification & Test Suite

- `tests/test_dpp_sampler.py`:
  - Test 1: Given 100 candidate mutants with high scores clustered in 2 sequence families, verify DPP batch selects equal representation from both families rather than greedily taking the top cluster.
- `tests/test_async_bo.py`:
  - Test 2: Ingest candidate $C_1$ as `PENDING_SYNTHESIS`. Run Round $N+1$ acquisition; verify $C_1$ and near-identical mutants receive acquisition score $\to 0$, forcing search into novel basins.
- `tests/test_telemetry_ingestion.py`:
  - Test 3: Ingest interim Day 10 crude LCMS data ($15\%$ purity); verify candidate moves to `SYNTHESIS_FAILED` and updates manufacturability model without waiting for bioassays.
