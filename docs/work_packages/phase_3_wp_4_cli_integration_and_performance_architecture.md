# Phase 3 — Work Package 4: CLI Integration & Performance Architecture

**Module Location:** `src/peptide_flywheel/workflows.py`, `scripts/validate_agent_output.py`, `docs/12_language_and_performance_architecture.md`  
**Language Standard:** UK English  

---

## 1. Executive Summary & Core Rationale

### 1.1 The Two-Language Symbiosis Standard
A complete rewrite of the scientific platform into C++ or Rust is counterproductive because **over 99.9% of total round latency** is dominated by physical wet-lab turnaround (2–6 weeks), GPU molecular dynamics (hours), and remote LLM API calls (seconds). High-level Python orchestration takes $<10\text{ ms}$.

**The Architectural Division of Labour:**
* **Python (Top-Level Orchestration & ML Bridges):** Controls the Research DAG, agent contracts, Pydantic schemas, and PyTorch / ESM-2 model interfaces.
* **Rust via PyO3 / Maturin (Computational Hotspots):** Dropped in strictly when candidate pool scales to $>100,000$ sequences for high-throughput SIMD biological DRC screening and combinatorial enumeration.
* **C++ / CUDA (Hardware Kernels):** Used transparently via native bindings (OpenMM, RDKit, LibTorch).

---

## 2. In-Workflow Biological DRC Execution (`workflows.py`)

In [`src/peptide_flywheel/workflows.py`](file:///Users/michaeladesiyan/Projects/peptide_discovery_flywheel_scaffold/src/peptide_flywheel/workflows.py), the biological DRC engine is integrated directly into the candidate scoring loop:
* Evaluates Henderson-Hasselbalch net charge at pH 7.4 (`drc_net_charge_ph74`).
* Evaluates Kyte-Doolittle hydropathicity (`drc_gravy_index`).
* Computes hard DRC status (`drc_passed_hard_drc`).
* Merges concrete chemical remediation notes into candidate cards in the Research DAG.

---

## 3. Ponytail Code-Simplification Standard

Before committing code, every module undergoes a Ponytail audit to prevent creeping over-engineering:
* **`shrink`:** Replaces verbose manual slice loops and temporary dataclasses with Python standard-library idioms (`collections.deque(maxlen=N)`, `collections.Counter`).
* **`native`:** Uses vectorized NumPy broadcasting for distance and matrix operations, avoiding unneeded third-party dependencies (`scipy.spatial.distance.cdist`).
* **`delete`:** Eliminates dead imports and unreferenced intermediate arrays.
