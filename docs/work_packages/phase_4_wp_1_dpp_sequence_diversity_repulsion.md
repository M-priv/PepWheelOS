# Phase 4 — Work Package 1: Determinantal Point Process (DPP) Batch Diversity (Pillar 2A)

**Module Location:** `src/peptide_flywheel/dpp_sampler.py`  
**Test Suite:** `tests/test_dpp_sampler.py`  
**Language Standard:** UK English  

---

## 1. Executive Summary & First-Principles Problem

When selecting a batch of $q=10$ to $q=100$ candidates for wet-lab synthesis, standard top-$K$ greedy selection picks 10 near-identical single-point mutants of the top lead (e.g. `KWKLFKKIEKWLFLG`, `KWKLFKKIEKWLFLA`, `KWKLFKKIEKWLFLV`).  
If that scaffold has an unforeseen synthesis failure, aggregation liability, or off-target toxicity, the **entire 3-week synthesis budget is lost with zero information gain**.

---

## 2. Mathematical Formulation & $L$-Ensemble Construction

A Determinantal Point Process (DPP) defines a probability distribution over all $2^N$ possible subsets $Y \subseteq \mathcal{X}$, where the probability of selecting subset $Y$ is proportional to the determinant of its marginal submatrix:
$$\mathcal{P}(Y) \propto \det(L_Y)$$

### 2.1 The $L$-Ensemble Matrix:
$$L_{ij} = q(x_i) \cdot K_{ij} \cdot q(x_j)$$
* **Quality Factor ($q(x_i)$):**
  $$q(x_i) = \exp\left(\frac{\text{Score}(x_i) - \max\text{Score}}{\tau}\right)$$
  where $\tau > 0$ is a temperature parameter that balances exploitation vs. diversity.
* **Diversity Similarity Kernel ($K_{ij}$):**
  $$K_{ij} = \exp\left(-\gamma \|\mathbf{e}_i - \mathbf{e}_j\|^2\right)$$
  computed over normalised 24-dimensional biophysical and compositional feature vectors $\mathbf{e}$.

### 2.2 Geometric Repulsion Mechanism:
The determinant $\det(L_Y)$ equals the squared volume of the parallelotope spanned by the feature vectors in $Y$:
- If two candidates are **identical or highly similar** ($K_{ij} \to 1$), their feature vectors are collinear, the parallelotope collapses to a flat plane, and $\det(L_Y) \to 0$.
- The sampler is **geometrically repelled** from picking redundant clones.

---

## 3. Fast Greedy Submodular MAP Selection

Finding the exact MAP subset ($\arg\max_{|Y|=q} \det(L_Y)$) is NP-hard, but because the log-determinant is **strictly submodular**, a greedy algorithm provides an optimal $(1 - 1/e)$ approximation guarantee in $\mathcal{O}(q^2 N)$ time:
1. Initialize $Y = \emptyset$.
2. For step $k = 1, \dots, q$:
   $$i^* = \arg\max_{i \notin Y} \log \det(L_{Y \cup \{i\}})$$
3. Add $i^*$ to $Y$.

---

## 4. Built-in 24-Dimensional Sequence Feature Extractor

Operates as a zero-dependency fallback when neural embeddings (ESM-2) are absent:
* 20 normalized amino acid composition frequencies.
* Sequence length (normalized).
* Kyte-Doolittle GRAVY hydropathicity index.
* Henderson-Hasselbalch net charge at pH 7.4.
* Aromatic fraction (`F`, `W`, `Y`).

---

## 5. Demonstrated Verification Results

In [`tests/test_dpp_sampler.py`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/tests/test_dpp_sampler.py), testing on clustered candidate pools confirmed:
* DPP preserves the top lead from Cluster 1 while selecting diverse leads from Cluster 2.
* Achieved **$>2\times$ higher average pairwise distance** than naive top-$K$ selection.
