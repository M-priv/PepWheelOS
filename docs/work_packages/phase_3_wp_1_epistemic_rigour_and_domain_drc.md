# Phase 3 — Work Package 1: Epistemic Rigour & Domain DRC (Pillar 1)

**Module Location:** `src/peptide_flywheel/contracts.py`, `src/peptide_flywheel/domain_drc.py`, `src/peptide_flywheel/dialectic.py`  
**Test Suites:** `tests/test_domain_drc.py`, `tests/test_dialectic.py`  
**Language Standard:** UK English  

---

## 1. Executive Summary & First-Principles Problem

In software engineering, schema validation (e.g. JSON schema, Pydantic) confirms that a payload is **syntactically well-formed** (e.g., `sequence` is a string, `score` is a float).  
However, in physical drug discovery, **an output can be 100% syntactically valid yet physically impossible, toxic, or unmanufacturable**. For example:
- A sequence containing `DG` (Asp-Gly) is a valid string, but undergoes base-catalysed aspartimide cyclisation in solid-phase peptide synthesis (SPPS), destroying chemical yield.
- A sequence containing `VVVLL` is valid text, but forms irreversible $\beta$-sheet amyloid fibrils that clog synthesis resin and precipitate during purification.
- LLMs suffer from **sycophancy and self-justifying optimistic bias**, hallucinating rationale to defend their own flawed proposals.

---

## 2. Mathematical & Architectural Mechanisms

### 2.1 Assume-Guarantee Formal Contracts (`contracts.py`)
Modeled after aerospace (NASA flight systems) and formal electronic design automation (EDA) methods:
- Every agent transformation is wrapped with `@enforce_contract`.
- **Preconditions (*Assumptions*):** Enforces sequence alphabet, length bounds, and non-null input contexts before executing expensive computational tools.
- **Postconditions (*Guarantees*):** Validates that all scores are finite, predicted properties conform to bounds, and no NaN/null values exist.

### 2.2 Biological Design Rule Checking (DRC) Suite (`domain_drc.py`)
Modeled after semiconductor VLSI layout checks, running deterministic physical invariant scans:
* **`DRC-001 (Aspartimide Cyclisation)`**: Flags base-catalysed succinimide ring formation at `D[GNS]` motifs.
* **`DRC-002 (Poly-Hydrophobic Collapse)`**: Flags $\ge 5$ consecutive aliphatic/aromatic residues (`[VILFYW]{5,}`) prone to on-resin aggregation.
* **`DRC-003 (Isoelectric Precipitation)`**: Solves Henderson-Hasselbalch charge equilibrium; flags neutral peptides ($|\text{charge}| < 0.5$ at pH 7.4) with hydropathy $>0.0$ that precipitate in physiological formulation.
* **`DRC-004 (Unpaired Cysteine Oxidation)`**: Flags odd numbers of cysteines that form scrambled intermolecular disulphide polymers.
* **`DRC-005 (Steric Poly-Proline Clashes)`**: Detects $[P]{3+}$ rigid conformational locks.

### 2.3 Adversarial Dialectic Committee (`dialectic.py`)
Pits an **Advocate Agent** against an independent **Sceptic Agent**:
- **Advocate:** Tasked with identifying positive binding mechanisms and target complementarity.
- **Sceptic:** Tasked exclusively with finding failure modes, chemical liabilities, and manufacturing risks.
- An SMT/Rule Arbiter computes the dissensus metric:
  $$\Delta_{\text{dissensus}} = |\text{Score}_{\text{advocate}} - \text{Score}_{\text{sceptic}}|$$
- When $\Delta_{\text{dissensus}} > 0.35$, the candidate is automatically flagged as high-epistemic-uncertainty and routed to targeted assay design rather than unhedged scale-up.
