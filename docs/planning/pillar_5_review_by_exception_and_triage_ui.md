# Deep Implementation Plan: Pillar 5 — Review-by-Exception & Apple HIG Scientist Triage UI

**Phase Alignment:** Phase 3 (Pareto/Conformal Math) & Phase 5 (Portfolio & Apple HIG Triage Workbench)  
**Target Codebase Location:** `src/peptide_flywheel/pareto_sort.py`, `src/peptide_flywheel/conformal.py`, `src/peptide_flywheel/triage_engine.py`, `src/peptide_flywheel/ui/`

---

## 1. Executive Summary & Problem Formulation

In high-throughput peptide campaigns, generating hundreds of candidate cards causes severe **human decision fatigue**. When scientists are forced to linearly inspect dense markdown reports for 50+ candidates, they become a rubber-stamping bottleneck.

Pillar 5 eliminates the review bottleneck through:
1. **"Review-by-Exception" Tri-State Funnel:** Automatically filtering out **$85\%$** of candidates ($70\%$ Auto-Green for clear winners, $15\%$ Auto-Red for fatal liabilities), routing only the **$15\%$** ambiguous/high-uncertainty cases to human scientists.
2. **Multi-Objective Non-Dominated Pareto Sorting (NSGA-II):** Presenting trade-off frontiers across Potency, Synthesizability, Solubility, and Selectivity.
3. **Split Conformal Prediction:** Providing distribution-free $90\%$ statistical coverage intervals to detect out-of-distribution hallucinations.
4. **Apple HIG-Inspired Triage Interface:** A glassmorphic, keyboard-first UI (`J/K/A/R`, `rounded-[2rem]`) with 3-level progressive disclosure (Orbit $\to$ Radar Glyph $\to$ Forensic AST Drawer).

---

## 2. Mathematical & Algorithmic Specifications

### 2.1 "Review-by-Exception" Tri-State Automated Funnel

```
Total Generated Candidate Pool (N = 100)
                 │
                 ▼
     [Tri-State Gating Rules Engine]
     ├───────────────────────────────────────────────────────┐
     ▼                                                       ▼
[AUTO_GREEN: 70%]               [AUTO_RED: 15%]       [AMBER_TRIAGE: 15%]
• Potency Score ≥ 0.80          • Fatal DRC Liabilities • Conflicting Pareto Trade-offs
• Manufacturability ≥ 0.85      • Aspartimide Motifs    • High Epistemic Uncertainty
• Risk Flag Count = 0           • Hydrophobic Collapse  • Conformal Interval Width > τ
• Conformal Width ≤ τ           • Aggregation Index > 0.90
     │                               │                       │
     ▼                               ▼                       ▼
Auto-Queued for Synthesis       Auto-Rejected & Tagged  ★ SCIENTIST TRIAGE WORKBENCH ★
(Audit Trail Logged)            in Failure Ontology     (Focused Review on 15 leads)
```

---

### 2.2 Multi-Objective Non-Dominated Pareto Sorting (NSGA-II)

Peptide discovery requires optimizing conflicting objectives:
$$\max_{\mathbf{x}} \quad \mathbf{F}(\mathbf{x}) = \left[ f_{\text{potency}}(\mathbf{x}), f_{\text{manufacturability}}(\mathbf{x}), f_{\text{solubility}}(\mathbf{x}), -f_{\text{toxicity}}(\mathbf{x}) \right]$$

1. **Dominance Definition:** $\mathbf{x}_1 \succ \mathbf{x}_2$ iff $\forall i, F_i(\mathbf{x}_1) \ge F_i(\mathbf{x}_2) \land \exists j, F_j(\mathbf{x}_1) > F_j(\mathbf{x}_2)$.
2. **Fast Non-Dominated Sorting:** Partitions candidate library into ranks $\mathcal{F}_1, \mathcal{F}_2, \dots, \mathcal{F}_k$.
3. **Hypervolume ($HV$) Contribution & Diversity Clustering:**
   - On Pareto Front $\mathcal{F}_1$, run K-Medoids clustering on ESM-2 embeddings to select $K$ structurally diverse non-dominated exemplars for the scientist.

---

### 2.3 Split Conformal Prediction for Guaranteed Coverage

To prevent overconfidence from black-box surrogate models, we compute distribution-free prediction intervals:

1. **Calibration Set:** $\mathcal{D}_{\text{cal}} = \{(x_i, y_i)\}_{i=1}^n$ of experimentally validated historical peptides.
2. **Non-Conformity Scores:** $s_i = |y_i - \hat{\mu}(x_i)|$.
3. **Conformal Quantile:** For user coverage $1 - \alpha = 0.90$:
   $$\hat{q} = \text{Quantile}\left(\{s_i\}_{i=1}^n, \frac{\lceil(n+1)(1-\alpha)\rceil}{n}\right)$$
4. **Prediction Interval:**
   $$C(x_{\text{new}}) = \left[ \hat{\mu}(x_{\text{new}}) - \hat{q}, \hat{\mu}(x_{\text{new}}) + \hat{q} \right], \quad \mathbb{P}(y_{\text{new}} \in C(x_{\text{new}})) \ge 0.90$$
5. **Gating Rule:** If interval width $2\hat{q} > \tau_{\text{uncertainty}}$, flag candidate as *High Epistemic Uncertainty* and route to Amber Triage.

---

## 3. Apple HIG-Inspired Triage Interface Architecture

The scientist triage interface is designed strictly around Apple Human Interface Guidelines (HIG): **Clarity, Deference, and Depth**.

```
+-----------------------------------------------------------------------------------+
|  FLYWHEEL OS   |   Target: CAMP-001 (Pseudomonas AMP)   |   Triage Queue: 14 Leads |
+-----------------------------------------------------------------------------------+
|  [ LEVEL 1: ORBITAL KPI BAR (Glassmorphic) ]                                      |
|  • Pareto Front Yield: 18%  • High Uncertainty: 6  • Auto-Passed: 72  • Auto-Red: 14|
+-----------------------------------------------------------------------------------+
|  [ LEVEL 2: ACTIVE TRIAGE CARD (rounded-[2.5rem], shadow-2xl) ]                    |
|                                                                                   |
|  Candidate: CAND-0042        Sequence: KWKLFKKIEKWLFLG-NH2                        |
|  ───────────────────────────────────────────────────────────────────────────────  |
|  RADAR PROFILE:                   PREDICTED TRADE-OFFS:                           |
|  Potency:         0.92 [±0.08]    • Synthesis Risk: Low (Score: 0.88)             |
|  Manufacture:     0.84            • Dialectic Dissensus: Moderate (Δ = 0.28)      |
|  Solubility:      0.78            • Red-Team Flag: Weak amphipathic hinge         |
|  Novelty:         0.89                                                            |
|                                                                                   |
|  DECISION CONTROLS (Keyboard-First):                                              |
|  [ A: Advance to Synthesis ]   [ R: Reject (Select 1-4) ]   [ Space: Open Drawer ]|
+-----------------------------------------------------------------------------------+
|  [ LEVEL 3: FORENSIC AST DRAWER (Slide-Over, Press Space) ]                       |
|  • Full AST JSON Diff  • ESM-2 Attention Contact Map  • Causal Falsification Log  |
+-----------------------------------------------------------------------------------+
```

### Design System Specification
* **Surfaces & Glassmorphism:**
  `backdrop-blur-xl bg-white/70 dark:bg-zinc-900/75 border border-white/20 dark:border-white/10 shadow-2xl`
* **Organic Radii:** `rounded-[2rem]` for sub-cards, `rounded-[2.5rem]` for main triage card container.
* **Typography:** SF Pro Display / Inter with tabular figures (`font-feature-settings: "tnum"`).
* **Keyboard-First Controls:**
  * `J` / `K`: Navigate Next / Previous Candidate.
  * `A`: Advance Candidate to Synthesis Batch.
  * `R`: Reject Candidate (triggers instant modal: `1`=Purity, `2`=Aggregation, `3`=Binding, `4`=Toxicity).
  * `Space`: Toggle Slide-Over Forensic AST Drawer.
  * `Cmd+K`: Quick Command Palette.

---

## 4. Implementation Steps & Milestones

1. **`src/peptide_flywheel/pareto_sort.py`**:
   - Implement fast non-dominated sorting algorithm ($\mathcal{O}(M N^2)$).
   - Implement hypervolume contribution and K-Medoids diversity exemplar selection.
2. **`src/peptide_flywheel/conformal.py`**:
   - Implement Split Conformal Prediction calibration and interval evaluator.
3. **`src/peptide_flywheel/triage_engine.py`**:
   - Implement tri-state router (`classify_candidate_triage_bucket()`).
   - Implement decision audit logger (`record_triage_decision()`).
4. **`src/peptide_flywheel/ui/` & `scripts/run_triage_workbench.py`**:
   - Implement standalone interactive HTML/Vanilla CSS/FastAPI triage dashboard.
   - Implement keyboard event listener bindings (`J/K/A/R/Space`).
   - Implement 3-level progressive disclosure components.

---

## 5. Verification & Test Suite

- `tests/test_pareto_conformal.py`:
  - Test 1: Given 50 multi-objective candidates, verify candidate with high potency and high synthesizability dominates candidate with low values across all axes.
  - Test 2: Verify conformal prediction intervals cover $\ge 90\%$ of synthetic ground truth test samples.
- `tests/test_triage_engine.py`:
  - Test 3: Pass candidate batch of 100 items; verify $\sim 70\%$ are routed to `AUTO_GREEN`, $\sim 15\%$ to `AUTO_RED`, and $\sim 15\%$ to `AMBER_TRIAGE`.
- `tests/test_ui_workbench.py`:
  - Test 4: Verify FastAPI backend properly registers keyboard triage decisions and updates the DAG.
