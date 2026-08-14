# Language & Performance Architecture: The Two-Language Symbiosis

**Document ID:** `DOC-ARCH-012`  
**Status:** Approved Architectural Standard  
**Pattern:** Python-First Orchestration & Bio-ML with Selective Rust Extensions (PyO3 / Maturin)

---

## 1. Executive Summary

The **Peptide Discovery Flywheel** adopts the modern industry-standard **Two-Language Symbiosis** (popularized by `pydantic-core`, `polars`, `tokenizers`, and `vLLM`):
* **Python (Top-Level & Orchestration):** Research DAG, agent contracts, dialectical reasoning, active learning policies, Pydantic schemas, and interfaces to PyTorch/ESM-2/RDKit.
* **Rust via PyO3 (Computational Hotspots):** High-throughput combinatorial sequence generation, SIMD biological DRC screening, and large-scale Determinantal Point Process (DPP) matrix inversions.
* **C++ / CUDA (Underlying Hardware Kernels):** Leveraged transparently through existing Python bindings (PyTorch, OpenMM, RDKit, GROMACS).

---

## 2. Latency Hierarchy & Computational Profile

Rewriting the entire platform in C++ or Rust is counterproductive because high-level language execution accounts for **less than 0.1%** of total round latency:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SYSTEM LATENCY HIERARCHY                              │
└─────────────────────────────────────────────────────────────────────────────┘
  1. Physical Wet-Lab Turnaround: 2 to 6 Weeks (SPPS & Assays)  ◄── Bound by physical chemistry
  2. 3D Molecular Dynamics / Structure: Hours (CUDA / GPU)      ◄── Bound by GPU compute
  3. Remote LLM & Foundation Model APIs: 500ms – 5s per call    ◄── Bound by network & remote GPU
  4. Python Orchestration, Contracts, DRC & DAG: 1ms – 10ms     ◄── CPU / Memory (negligible)
```

---

## 3. The 3-Tier Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PYTHON ORCHESTRATION & AGENT LAYER                                       │
│    • Research DAG & Campaign Memory (`networkx`, `sqlite`, `pydantic`)       │
│    • Agent Contracts & Epistemic Firewall (`contracts.py`, `dialectic.py`)  │
│    • Bio-ML Surrogates & Language Models (`torch`, `esm`, `botorch`)        │
│    • API & Triage Interface (`fastapi`, `asyncio`)                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ PyO3 C ABI Bindings
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. RUST COMPUTATIONAL CORE (`peptide_flywheel_core` via Maturin)             │
│    • High-Throughput Combinatorial Sequence Enumeration (10^7 - 10^9 space)  │
│    • SIMD-Accelerated Biological DRC Invariant Scanning (Regex/pI/Hydropathy)│
│    • Fast NSGA-II Non-Dominated Sorting & k-DPP Greedy Matrix Inversions     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Native C++ / CUDA Driver
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. HARDWARE & SPECIALIST C++/CUDA KERNELS                                   │
│    • OpenMM / GROMACS (Molecular Dynamics)                                  │
│    • RDKit (Cheminformatics Graph Core)                                     │
│    • PyTorch LibTorch / FlashAttention (GPU Tensor Acceleration)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Rust Migration Trigger Thresholds

To maintain rapid development velocity without premature optimization, components remain in pure Python until specific scale triggers are reached:

| Module | Python Baseline Performance | Rust Port Trigger Condition | Target Rust Acceleration |
|---|---|---|---|
| **Domain DRC (`domain_drc.py`)** | $\sim 50,000\text{ sequences/sec}$ | Candidate screening library $> 100,000$ sequences | $\sim 5,000,000\text{ sequences/sec}$ (via Rayon + SIMD regex) |
| **Combinatorial Generator** | $\sim 10,000\text{ variants/sec}$ | Full combinatorial library $> 10^7$ permutations | $> 20,000,000\text{ variants/sec}$ |
| **DPP Sampler (`dpp_sampler.py`)** | $\sim 100\text{ ms for } q=50$ ($N=1,000$) | Library size $N > 50,000$ candidate embeddings | Sub-millisecond greedy submodular MAP |
| **Pareto Sorting (`pareto_sort.py`)** | $\mathcal{O}(M N^2)$ in NumPy | Library size $N > 20,000$ multi-objective points | Parallel non-dominated sort via Rust `rayon` |

---

## 5. Why Rust Over C++ for Scientific Systems

1. **Guaranteed Memory Safety:** Zero risk of buffer overflows, use-after-free, or segfaults crashing a long-running multi-day discovery campaign.
2. **Modern Toolchain (`cargo` & `maturin`):** Compiles seamlessly into native Python wheels (`.whl`) distributable via `pip`/`uv` without requiring complex C++ `CMake` or `vcpkg` setups.
3. **PyO3 Ergonomics:** Seamless bidirectional data exchange between Python types (`PyDict`, `PyList`, NumPy arrays) and Rust structs.
4. **Fearless Concurrency:** Built-in data-race prevention via `Rayon` for multi-threaded sequence scanning.

---

## 6. Directory Structure & Extension Conventions

When Rust extensions are introduced, they adhere to the standard `maturin` layout:

```
peptide_discovery_flywheel_scaffold/
├── Cargo.toml                      # Rust workspace manifest
├── crates/
│   └── peptide_flywheel_core/     # Rust native extension crate
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs              # PyO3 module entrypoint
│           ├── drc_scanner.rs      # SIMD Biological DRC
│           ├── dpp_kernel.rs       # Determinantal Point Process
│           └── pareto.rs           # Fast NSGA-II non-dominated sorting
├── src/
│   └── peptide_flywheel/           # Python package (imports from core)
│       ├── __init__.py
│       ├── domain_drc.py           # Python API with fallback to Rust core
│       └── ...
└── pyproject.toml                  # Maturin build backend configuration
```
