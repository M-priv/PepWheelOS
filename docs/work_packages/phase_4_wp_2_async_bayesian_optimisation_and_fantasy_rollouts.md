# Phase 4 — Work Package 2: Asynchronous Bayesian Optimisation & Monte Carlo Fantasies (Pillar 2B)

**Module Location:** `src/peptide_flywheel/async_bo.py`  
**Test Suite:** `tests/test_async_bo.py`  
**Language Standard:** UK English  

---

## 1. Executive Summary & First-Principles Problem

In peptide drug discovery, physical synthesis (SPPS) and wet-lab bioassays take **2 to 6 weeks per round**, whilst computational generation takes seconds.  
Sequential optimisation ($q=1$) leaves the synthesis lab sitting idle for a month waiting for results.  
However, if we attempt to design Round $N+1$ without Round $N$'s results, standard optimisers treat the in-flight candidates as unmeasured, predicting high uncertainty in that exact region and proposing **near-duplicate clones of in-flight candidates**, wasting budget on redundant assays.

---

## 2. Mathematical Foundation & Key Theorems

### 2.1 The Fundamental Theorem: Why Mean Depends on Lab Outcomes, but Variance Does Not
In Gaussian Process conditioning over measured data $\mathbf{y}$ and a test candidate $x^*$:
* **Conditional Mean:**
  $$\mu(x^*) = \mathbf{k}_*^T (\mathbf{K} + \sigma_n^2 \mathbf{I})^{-1} \mathbf{y}$$
  *(Contains $\mathbf{y}$ at the end: the expected height is a linear combination of physical lab measurements).*
* **Conditional Variance:**
  $$\sigma^2(x^*) = k(x^*, x^*) - \mathbf{k}_*^T (\mathbf{K} + \sigma_n^2 \mathbf{I})^{-1} \mathbf{k}_*$$
  *(Contains **NO** $\mathbf{y}$: uncertainty depends solely on coordinate locations $X$ and kernel distance).*

**The Flashlight Analogy:**  
Turning on a flashlight at location $X$ illuminates that spot (uncertainty $\sigma \to 0$) regardless of whether the light reveals treasure ($y=100$) or an empty floor ($y=0$).  
Therefore, the exact moment we queue candidate $X_{\text{pending}}$ for synthesis, **we can compute the future uncertainty map across the entire peptide library with 100% mathematical certainty weeks before the wet lab finishes**.

---

## 3. Monte Carlo Fantasy Worlds: Hedging vs. "Shooting Blind"

While the *variance* $\sigma^2(x)$ collapses deterministically, the *mean* $\mu(x)$ depends on whether $X_{\text{pending}}$ turns out to be a winner or a dud.

We sample $M=32$ correlated hypothetical outcomes from the joint GP posterior:
$$\tilde{\mathbf{y}}^{(m)} \sim \mathcal{N}\left(\boldsymbol{\mu}_{\text{pending}}, \mathbf{\Sigma}_{\text{pending}}\right)$$

### How the 32 Fantasy Worlds Protect the Campaign:
* **In worlds where Round $N$ is a WINNER ($\tilde{y}=9.5$):** The model focuses on fine-tuning mutations and capping modifications around the lead.
* **In worlds where Round $N$ is a DUD ($\tilde{y}=0.1$):** The model eliminates that chemical island and pivots to the second-best orthogonal scaffold.
* **The Asynchronous Portfolio ($\alpha_{\text{async}} = \frac{1}{M}\sum \alpha^{(m)}$):** Round $N+1$ constructs an optimal 50/50 hedge:
  - 50% follow-up bets on winning mutations.
  - 50% insurance bets on backup scaffolds (already in the synthesiser 3 weeks early if Round $N$ fails).

---

## 4. The 4 Physical Anchors Governing the Fantasies

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

## 5. Automated Telemetry Calibration & Scientist Review

When real wet-lab CSV/JSON data arrives:
1. **Automated MML Refitting (< 50ms):** The GP automatically updates length-scale $\ell$, signal amplitude $\sigma_f^2$, and assay noise $\sigma_n^2$ via Maximum Marginal Likelihood:
   $$\log p(\mathbf{y} \mid X, \boldsymbol{\theta}) = -\frac{1}{2} \mathbf{y}^T \mathbf{K}_{\boldsymbol{\theta}}^{-1} \mathbf{y} - \frac{1}{2} \log |\mathbf{K}_{\boldsymbol{\theta}}| - \frac{N}{2} \log(2\pi)$$
2. **Fantasy Dissolution:** The $M=32$ fantasy worlds are automatically deleted and collapse into the single, true empirical reality.
3. **Review-by-Exception:** Human scientists only intervene if an SRE anomaly is detected (e.g. assay noise $\sigma_n^2$ spikes $>3\times$ due to plate contamination or 0% batch synthesis yield).

---

## 6. Deep Dive: Cholesky Numerical Stability & The Eigenvalue Shift Theorem

### 6.1 The Core Failure Mode: Why Clustered or Identical Candidates Fail
When sampling correlated fantasy draws ($\tilde{\mathbf{y}} = \boldsymbol{\mu} + \mathbf{L}\boldsymbol{\epsilon}$), the algorithm computes the Cholesky factorisation $\mathbf{\Sigma} = \mathbf{L}\mathbf{L}^T$.  
If the candidate pool contains two identical (or heavily clustered) peptides ($x_1 \approx x_2$), their correlation is $K(x_1, x_2) = 1.0$:
$$\mathbf{\Sigma} = \begin{bmatrix} 1.0 & 1.0 \\ 1.0 & 1.0 \end{bmatrix}$$
* **Determinant:** $\det(\mathbf{\Sigma}) = (1.0 \times 1.0) - (1.0 \times 1.0) = \mathbf{0.0}$.
* **Eigenvalues:** $\lambda_1 = 2.0$, $\lambda_2 = \mathbf{0.0}$.

Cholesky decomposition strictly requires all eigenvalues to be strictly positive ($\lambda_i > 0$). When an eigenvalue is zero or slightly negative (due to 64-bit float rounding), standard LAPACK crashes with `LinAlgError: Matrix is not positive definite`.

### 6.2 The Mathematical Proof: The Eigenvalue Shift Theorem
When we add diagonal jitter $\epsilon \mathbf{I}$ (where $\epsilon = 10^{-6}$ and $\mathbf{I}$ is the Identity matrix):
$$\mathbf{\Sigma}_{\text{stable}} = \mathbf{\Sigma} + \epsilon \mathbf{I}$$

If $\mathbf{v}$ is an eigenvector of $\mathbf{\Sigma}$ with eigenvalue $\lambda$:
$$\mathbf{\Sigma}_{\text{stable}}\mathbf{v} = (\mathbf{\Sigma} + \epsilon \mathbf{I})\mathbf{v} = \mathbf{\Sigma}\mathbf{v} + \epsilon \mathbf{v} = \lambda \mathbf{v} + \epsilon \mathbf{v} = \mathbf{(\lambda + \epsilon)} \mathbf{v}$$

**Theorem Outcome:** Adding $\epsilon \mathbf{I}$ shifts every single eigenvalue upwards by exactly $+\epsilon$:
$$\lambda_i^{\text{new}} = \lambda_i + \epsilon$$

Even for 100% duplicate candidates where $\lambda_{\min} = 0.0$:
$$\lambda_{\min}^{\text{new}} = 0.0 + 10^{-6} = \mathbf{10^{-6} > 0}$$

Because all eigenvalues are mathematically guaranteed to be strictly positive ($\lambda_i > 0$), the matrix $\mathbf{\Sigma}_{\text{stable}}$ is **100% guaranteed to be strictly positive definite and invertible**, ensuring Cholesky sampling never crashes regardless of candidate similarity.

### 6.3 Why It Does Not Distort Biophysical Correlations
* $\epsilon = 10^{-6}$ is **one part in a million** ($0.0001\%$).
* Off-diagonal cross-correlations ($K_{12} = 0.950000$) remain completely untouched.
* Physically, $\epsilon = 10^{-6}$ represents an infinitesimal instrument noise floor, which accurately reflects real-world laboratory assays where zero-noise measurements do not physically exist.
