# Phase 3 — Work Package 3: Multi-Objective Pareto Sorting & Conformal Prediction (Pillars 3 & 5A)

**Module Location:** `src/peptide_flywheel/pareto_sort.py`, `src/peptide_flywheel/conformal.py`  
**Test Suite:** `tests/test_pareto_conformal.py`  
**Language Standard:** UK English  

---

## 1. Executive Summary & First-Principles Problem

### 1.1 The 1D Scalar Trap
In drug discovery, combining Potency, Synthesisability, Solubility, and Toxicity into a single weighted sum (e.g. $\text{Score} = 0.5 \cdot \text{Potency} + 0.5 \cdot \text{Solubility}$) creates **"cheater molecules"**:
- A peptide with 10/10 potency but 0/10 solubility gets a "5/10" and looks identical to an average peptide with 5/10 potency and 5/10 solubility.
- Real drug development requires trade-off navigation across orthogonal, competing objectives without scalar compression.

### 1.2 Uncalibrated AI Model Overconfidence
Deep learning models and LLMs frequently output 95% confidence on out-of-distribution molecules that fail in physical assays. Naive Gaussian error assumptions break down in high-dimensional sequence spaces.

---

## 2. Mathematical & Architectural Mechanisms

### 2.1 NSGA-II Fast Non-Dominated Sorting (`pareto_sort.py`)
Partitions the candidate library $\mathcal{X}$ into non-dominated Pareto fronts ($\mathcal{F}_1, \mathcal{F}_2, \dots$):
1. **Dominance Condition:** Candidate $p$ dominates $q$ ($p \succ q$) if $p$ is no worse than $q$ in all objectives, and strictly better in at least one:
   $$\forall k \in \{1, \dots, M\}, \quad f_k(p) \ge f_k(q) \quad \land \quad \exists j \text{ s.t. } f_j(p) > f_j(q)$$
2. **Front 1 ($\mathcal{F}_1$):** Contains all candidates that are dominated by no other candidate in the library.
3. **Crowding Distance Diversity:** Within any front, crowding distance measures the Euclidean cuboid perimeter around each candidate. Selecting candidates with maximum crowding distance prevents clustering on a single trade-off.

### 2.2 Split Conformal Prediction Intervals (`conformal.py`)
Provides **distribution-free finite-sample coverage guarantees** for property prediction surrogates:
1. **Calibration:** On a validation set $\{(x_i, y_i)\}_{i=1}^n$, compute absolute non-conformity residuals:
   $$R_i = |y_i - \hat{\mu}(x_i)|$$
2. **Conformal Quantile:** Compute the empirical $(1-\alpha)$ quantile $\hat{q}$ at level:
   $$p = \frac{\lceil (n+1)(1-\alpha) \rceil}{n}$$
3. **Prediction Interval:** For any new candidate $x^*$:
   $$C(x^*) = \left[ \hat{\mu}(x^*) - \hat{q}, \; \hat{\mu}(x^*) + \hat{q} \right]$$
4. **Coverage Guarantee:**
   $$P\left(y^* \in C(x^*)\right) \ge 1 - \alpha \quad (\text{e.g. } 90\% \text{ coverage for } \alpha = 0.10)$$
5. **Epistemic Gating:** If interval width $2\hat{q} > 0.35$, the candidate is automatically flagged as `is_high_uncertainty = True` and routed to the active learning queue.
