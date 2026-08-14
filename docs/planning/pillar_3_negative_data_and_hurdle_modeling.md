# Deep Implementation Plan: Pillar 3 — Decoupled Negative Data Learning & Causal Attribution

**Phase Alignment:** Phase 4 (Experimental Feedback, Negative Data & Asynchronous Loop)  
**Target Codebase Location:** `src/peptide_flywheel/hurdle_models.py`, `src/peptide_flywheel/tobit_gp.py`, `src/peptide_flywheel/causal_attribution.py`, `src/peptide_flywheel/ontology_sweeper.py`

---

## 1. Executive Summary & Problem Formulation

In naive AI drug discovery, experimental failure data is often mishandled in one of two catastrophic ways:
1. **Discarded / Ignored:** "Non-binding" or "synthesis failed" peptides are filtered out, creating severe survivor bias.
2. **Lumped into Scalar Objectives (Model Pollution):** Assigning dummy negative scores (e.g. $-\infty$ or $\text{IC}_{50} = 100\,\mu\text{M}$) to peptides that failed SPPS synthesis corrupts the spatial smoothness and spatial derivatives of the biological binding surrogate.

Pillar 3 implements:
* **Decoupled Hurdle Modeling:** Feasibility ($P(\text{synthesis \& solubility})$) is modeled separately from Potency ($f(x) \mid \text{feasible}$).
* **Tobit Right-Censored Likelihoods:** Retaining assay detection limits without gradient distortion.
* **Causal Failure Deconstruction:** Automatically attributing synthesis/assay drops to root-cause motifs in `04_failure_ontology.md`.
* **Retroactive Invariant Sweeping:** Background regression sweeper that continuously queries the historical DAG and flags legacy candidates whenever a new liability motif is discovered.

---

## 2. Mathematical & Algorithmic Specifications

### 2.1 Decoupled Hurdle Gaussian Process Architecture

```
Candidate Sequence x
        │
        ├──► Model 1: Feasibility Classifier P(Feasible | x)
        │    (Trained on ALL N_total attempted candidates: SPPS + QC)
        │
        └──► Model 2: Potency Regressor f_potency(x | Feasible)
             (Trained ONLY on soluble, purified, QC-passed binders)
        │
        ▼
Constrained Acquisition: α_EIC(x) = E[ max(0, y(x) - y*) ] * P(Feasible | x)
```

1. **Feasibility Classifier ($P(\text{Feasible} \mid x)$)**:
   * Binary classification using Laplace approximation or Gaussian Process Classification (GPC).
   * Models the joint probability:
     $$P(\text{Feasible} \mid x) = P(\text{Crude Purity} \ge 70\% \mid x) \times P(\text{Soluble} \mid x)$$
2. **Conditional Potency Regressor ($f_{\text{potency}}(x)$)**:
   * Gaussian Process regression over $d$-dimensional ESM-2 sequence embeddings:
     $$f(x) \sim \mathcal{GP}\left(\mu(x), k(x, x')\right)$$
   * Conditioned *strictly* on $D_{\text{feasible}} = \{(x_i, y_i) \mid \text{Feasible}(x_i) = \text{True}\}$.

---

### 2.2 Tobit Likelihood Engine for Right-Censored Bioassay Limits

When bioassays reach the detection limit (e.g., surface plasmon resonance floor at $\text{LOD} = 10\,\mu\text{M}$), inactive candidates are right-censored ($y > y_{\text{limit}}$).

**Tobit GP Likelihood Formulation:**
$$p(y_i \mid f(x_i)) = \begin{cases} \frac{1}{\sigma_n} \phi\left( \frac{y_i - f(x_i)}{\sigma_n} \right) & \text{if } y_i \text{ is exactly measured} \\ 1 - \Phi\left( \frac{y_{\text{limit}} - f(x_i)}{\sigma_n} \right) = \Phi\left( \frac{f(x_i) - y_{\text{limit}}}{\sigma_n} \right) & \text{if } y_i > y_{\text{limit}} \text{ (right-censored)} \end{cases}$$
where $\phi(\cdot)$ is the standard normal PDF and $\Phi(\cdot)$ is the standard normal CDF.

*Benefit:* Incorporates non-binding negative data by informing the model that the region is strictly worse than $y_{\text{limit}}$ without distorting the GP variance or flattening gradients.

---

### 2.3 Causal Motif Failure Deconstruction & Ontology Mapping

When experimental data arrives with a failure readout, the **Causal Failure Deconstructor** executes a rule-based decomposition:

| Experimental Observation | Mechanistic Cause | Ontology Tag (`04_failure_ontology.md`) | Remediating Design Constraint |
|---|---|---|---|
| Crude purity $< 30\%$, major $[M-18]$ peak in LCMS | Aspartimide ring closure at `DG`/`DS` | `SYN_MODIFICATION_FAILED` | Ban `DG`/`DS` or require $\alpha$-methyl aspartate |
| Truncated failure at residue 12; sequence has `VVVLL` | $\beta$-sheet on-resin aggregation | `SYN_HYDROPHOBIC_SEQUENCE` | Insert pseudoproline or PEG spacer |
| Purity $>95\%$, DLS shows $>100\text{ nm}$ aggregates | Colloidal self-association at neutral pH | `AGGREGATION` | Mutate hydrophobic face or increase net charge |
| No SPR binding at $50\,\mu\text{M}$; high purity monomer | True pocket mismatch | `NO_BINDING` | Refine target pocket coordinates |

---

### 2.4 Retroactive Invariant Sweeper

```python
class RetroactiveOntologySweeper:
    def __init__(self, dag_repository, failure_ontology):
        self.dag = dag_repository
        self.ontology = failure_ontology

    def on_new_liability_discovered(self, motif: str, failure_code: str, mechanism: str):
        # 1. Query all historical candidate cards in campaign DAG
        all_candidates = self.dag.get_all_candidates()
        
        flagged_candidates = []
        for cand in all_candidates:
            if motif in cand.sequence:
                # 2. Attach retroactive invalidation event to DAG node
                warning_event = {
                    "event_type": "RETROACTIVE_LIABILITY_WARNING",
                    "flagged_motif": motif,
                    "failure_code": failure_code,
                    "reason": mechanism,
                    "recorded_at": datetime.now(timezone.utc).isoformat()
                }
                self.dag.append_event_to_candidate(cand.candidate_id, warning_event)
                flagged_candidates.append(cand.candidate_id)
                
        return flagged_candidates
```

---

## 3. Data Structures & Schemas

```python
# src/peptide_flywheel/models.py additions
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class CensoringType(str, Enum):
    EXACT = "exact"
    LEFT_CENSORED = "left_censored"    # e.g., below assay limit of quantitation (< 0.1 nM)
    RIGHT_CENSORED = "right_censored"  # e.g., inactive / non-binder (> 10 uM)
    INTERVAL_CENSORED = "interval_censored"

class MultiFidelityAssayReadout(BaseModel):
    fidelity_tier: str  # "s0_in_silico", "s1_physics", "s2_crude_array", "s3_purified_wetlab"
    endpoint_name: str  # "ic50_nm", "kd_nm", "crude_purity_pct", "solubility_ug_ml"
    value: float
    censoring: CensoringType = CensoringType.EXACT
    censor_threshold: Optional[float] = None
    experimental_conditions: dict[str, Any] = Field(default_factory=dict)

class CausalFailureAttribution(BaseModel):
    candidate_id: str
    failure_code: str  # from 04_failure_ontology.md
    mechanistic_category: str  # "aspartimide", "hydrophobic_collapse", "steric_coupling"
    culprit_motif: Optional[str] = None
    sequence_positions: list[int] = Field(default_factory=list)
    counterfactual_remediation: str
    confidence: float
```

---

## 4. Implementation Steps & Milestones

1. **`src/peptide_flywheel/hurdle_models.py`**:
   - Implement Gaussian Process Feasibility Classifier for $P(\text{Feasible} \mid x)$.
   - Implement Conditional Potency GP trained exclusively on feasible subsets.
   - Implement $\alpha_{\text{EIC}}(x)$ constrained expected improvement.
2. **`src/peptide_flywheel/tobit_gp.py`**:
   - Implement Tobit right-censored log-likelihood and gradient evaluations.
   - Add unit tests verifying stability on $>10\,\mu\text{M}$ assay readouts.
3. **`src/peptide_flywheel/causal_attribution.py`**:
   - Implement heuristic failure deconstruction rules mapping LCMS/purity anomalies to ontology codes.
4. **`src/peptide_flywheel/ontology_sweeper.py`**:
   - Implement background regression sweeper that walks DAG nodes and logs retroactive warnings.

---

## 5. Verification & Test Suite

- `tests/test_hurdle_models.py`:
  - Test 1: Train hurdle model on 50 synthetic peptides where 10 failed synthesis (purity $<10\%$). Verify potency model predictions are uncorrupted by synthesis failures.
- `tests/test_tobit_gp.py`:
  - Test 2: Train Tobit GP with 30 exact measurements and 20 right-censored ($>10\,\mu\text{M}$) points. Verify predictive variance is smaller than discarding censored rows, and mean in censored region is $>10\,\mu\text{M}$.
- `tests/test_causal_sweeper.py`:
  - Test 3: Insert a new failure rule for motif `"DG"`. Verify historical candidates containing `"DG"` are flagged with `RETROACTIVE_LIABILITY_WARNING`.
