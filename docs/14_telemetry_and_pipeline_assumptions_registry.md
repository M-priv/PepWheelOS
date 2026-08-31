# Telemetry & Experimental Pipeline Assumptions Registry

**Document ID:** `DOC-ASSUMP-014`  
**Status:** Living Engineering Standard & Calibration Registry  
**Language Standard:** UK English  
**Associated Modules:** `src/peptide_flywheel/telemetry_ingestion.py`, `src/peptide_flywheel/async_bo.py`, `src/peptide_flywheel/dpp_sampler.py`  

---

## 1. Executive Summary & Purpose

In computational biology and automated drug discovery pipelines, algorithms frequently encode implicit assumptions about wet-lab chemistry, assay kinetics, and CRO operations. If left unmonitored, these assumptions can lead to:
1. **False Rejections:** Discarding viable therapeutic candidates due to rigid or uncalibrated physical thresholds.
2. **Model Poisoning:** Ingesting assay artifacts (e.g. colloidal aggregators or lot-to-lot assay drift) as high-affinity ground truth.
3. **Operational Blindspots:** Assuming rigid calendar turnaround times when physical synthesis schedules vary widely.

This registry catalogues every key assumption across the experimental pipeline, details its underlying failure modes, and defines concrete calibration protocols.

---

## 2. Mass Spectrometry & Analytical Chemistry Assumptions

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            ANALYTICAL CHEMISTRY ASSUMPTIONS                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Monoisotopic vs. Average Molecular Weight Thresholds
* **Built-In Assumption:** Mass error tolerance is bounded by $|M_{\text{observed}} - M_{\text{expected}}| \le 1.0\text{ Da}$ or $< 500\text{ ppm}$.
* **Physical Failure Mode:** For larger peptide therapeutics ($>30$ residues, $>3,500\text{ Da}$), the natural abundance of $^{13}\text{C}$ ($1.1\%$) and $^{15}\text{N}$ shifts the **average molecular weight** $2\text{--}3\text{ Da}$ higher than the **monoisotopic weight** (which considers only $^{12}\text{C}$ and $^{14}\text{N}$). If a CDMO instruments exports average mass whilst the pipeline computes monoisotopic mass, valid long peptides will be falsely rejected with `SYN_WRONG_MASS`.
* **Calibration Protocol:**
  - Track whether the CDMO spectrometer reports monoisotopic $[M+H]^+$ / $[M+2H]^{2+}$ or deconvoluted average mass.
  - Apply dynamic tolerance scaling: for peptides with length $N > 30$, expand the allowable mass window to $\pm 2.5\text{ Da}$ when average molecular weight is supplied.

### 2.2 Crude Purity Purification Yield Assumption
* **Built-In Assumption:** Any peptide with $\ge 40\%$ crude LCMS purity can be successfully purified by preparative reverse-phase HPLC to $\ge 90\%$ purity with $>1.0\text{ mg}$ recovery.
* **Physical Failure Mode:** If crude synthesis impurities include closely eluting deletion sequences (e.g. $N-1$ deletion of a single hydrophobic residue) with identical retention times, preparative HPLC separation becomes impossible, resulting in $<5\%$ recovery and insufficient material for SPR assays.
* **Calibration Protocol:**
  - Monitor the historical **Crude-to-Purified Conversion Rate** in the Research DAG.
  - Automatically flag sequences with high predicted hydropathicity gradients for double-coupling SPPS protocols if conversion rate drops below $70\%$.

### 2.3 Isobaric Isomerisation Invariance
* **Built-In Assumption:** Matching expected mass confirms correct primary structure and chemical integrity.
* **Physical Failure Mode:** Isobaric chemical modifications yield identical mass but destroy biological activity:
  - *Aspartimide Hydrolysis:* Produces iso-aspartate ($\beta$-peptide bond) with exact identical mass.
  - *Disulphide Scrambling:* 4 cysteines forming wrong pairwise linkages (1–3, 2–4 instead of 1–4, 2–3).
  - *Leu / Ile Scramble:* Exact identical residue mass ($113.16\text{ Da}$).
* **Calibration Protocol:**
  - Never declare biological success on mass match alone.
  - Require Stage 2 analytical HPLC retention time matching and Stage 3 SPR binding kinetics before confirming hit validation.

---

## 3. Formulation, Solubility & Biophysical Assumptions

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            BIOPHYSICAL & FORMULATION ASSUMPTIONS                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 PBS at pH 7.4 as the Sole Solubility Benchmark
* **Built-In Assumption:** Candidates must exhibit aqueous solubility $\ge 0.5\text{ mg/mL}$ in phosphate-buffered saline (PBS) at pH 7.4.
* **Physical Failure Mode:** Many highly potent therapeutic leads targeting hydrophobic protein-protein interaction (PPI) interfaces or transmembrane receptors are poorly soluble in pure aqueous buffer, but fully soluble and stable in formulation cosolvents ($1\text{--}2\%$ DMSO, PEG-300, or histidine buffer at pH 6.5). Hard-rejecting in pure PBS discards viable intracellular lead series.
* **Calibration Protocol:**
  - Implement a two-tiered solubility test: candidates failing pure PBS solubility undergo secondary testing in assay buffer with $1\%$ DMSO cosolvent before triggering a hard `SOLUBILITY_LOW` rejection.

### 3.2 Dynamic Light Scattering (DLS) Polydispersity as Complete Aggregation Filter
* **Built-In Assumption:** DLS Polydispersity Index (PDI) $\le 0.30$ guarantees the absence of aggregation liabilities.
* **Physical Failure Mode:** While DLS accurately detects large colloidal aggregates and micelles ($>50\text{ nm}$), it has lower sensitivity for small soluble oligomers (dimers, trimers, or tetramers) that can cause non-specific promiscuous binding.
* **Calibration Protocol:**
  - For top-tier validated lead candidates progressing to in vivo testing, supplement DLS with Analytical Size-Exclusion Chromatography (SEC-HPLC) to resolve oligomeric states.

---

## 4. Bioassay & Surface Plasmon Resonance (SPR) Assumptions

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            BIOASSAY & KINETICS ASSUMPTIONS                                       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 1:1 Langmuir Bimolecular Binding Model
* **Built-In Assumption:** SPR sensograms follow standard 1:1 Langmuir interaction kinetics ($A + B \rightleftharpoons AB$) yielding $K_d = k_{\text{off}} / k_{\text{on}}$.
* **Physical Failure Mode:** Complex mechanisms (target homodimerisation, two-state induced-fit conformational changes, or bivalent avidity) produce bi-phasic sensogram curves. Fitting a 1:1 model to a two-state system produces artificially inaccurate $K_d$ estimates.
* **Calibration Protocol:**
  - Inspect residual curvature ($\chi^2$) of the SPR kinetic fit; if $\chi^2 > 10\%$ of $R_{\max}$, flag the candidate for multi-state kinetic evaluation.

### 4.2 Cross-Batch and Inter-Run Assay Consistency
* **Built-In Assumption:** A binding affinity measurement of $K_d = 50\text{ nM}$ from Round 1 is directly comparable on the same scalar scale as $K_d = 50\text{ nM}$ measured two months later in Round 3.
* **Physical Failure Mode:** CRO instrument drift, variations in target protein immobilisation density (RU levels), sensor chip lot differences, and ambient temperature shifts introduce inter-batch assay variance.
* **Calibration Protocol:**
  - Every assay plate must include standard reference benchmark controls (e.g. `LIT-AMP-001`) with known affinity.
  - Normalise raw $K_d$ values relative to the control's fold-shift across batches.

---

## 5. Machine Learning & Bayesian Optimisation Assumptions

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        ALGORITHMIC & ASYNCHRONOUS BO ASSUMPTIONS                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Synthesis Feasibility and Binding Potency are Decoupled
* **Built-In Assumption:** Standard regression models treat synthesis yield and biological potency as independent variables.
* **Physical Failure Mode:** In structural biology, the bulky aromatic and hydrophobic residues (`W`, `F`, `Y`, `L`) that drive high-affinity target engagement often cause severe on-resin steric hindrance and aggregation during SPPS.
* **Calibration Protocol:**
  - **Solved in Work Package 4 (Decoupled Hurdle Modelling):** Explicitly model the joint distribution via a two-part Hurdle GP, learning how sequence properties affect both the binary feasibility classifier and the potency regressor simultaneously.

### 5.2 Independent Event-Driven Batch Telemetry
* **Built-In Assumption:** Staggered physical deliveries for candidates occur independently per peptide ID.
* **Physical Failure Mode:** In high-throughput 96-well peptide synthesizers, instrument failures (e.g. nitrogen manifold pressure loss or cleavage block drain clog) affect entire physical plates simultaneously.
* **Calibration Protocol:**
  - Track CDMO plate identifiers (`plate_id`, `well_position`); if $>50\%$ of candidates on a single plate fail simultaneously, trigger an automated `BATCH_PLATE_FAILURE` alert rather than penalising individual sequence designs.

---

## 6. Assumptions Audit & Calibration Schedule

| Assumption Category | Key Risk | Verification Hook in Codebase | Audit Frequency |
|---|---|---|---|
| **Mass Accuracy** | Monoisotopic vs. average MW discrepancy | [`telemetry_ingestion.py:L36-41`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/telemetry_ingestion.py#L36-L41) | Per CDMO onboarding |
| **Solubility Thresholds** | Discarding hydrophobic leads | [`telemetry_ingestion.py:L62-65`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/telemetry_ingestion.py#L62-L65) | Per campaign target |
| **SPR Kinetics** | Two-state vs. 1:1 Langmuir kinetics | [`telemetry_ingestion.py:L82-93`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/telemetry_ingestion.py#L82-L93) | Post-Round review |
| **Assay Batch Drift** | Chip lot & temperature drift | Reference control normalisation | Per assay run |
| **Synthesis/Potency Coupling** | Correlated negative data | `hurdle_gp.py` (Work Package 4) | Continuous active learning |
