# Deep Implementation Plan: Pillar 4 — SRE Agent Runtime & Content-Addressed Storage

**Phase Alignment:** Phase 3 (Scientific Tooling, Epistemic Rigor & SRE Runtime)  
**Target Codebase Location:** `src/peptide_flywheel/cas_store.py`, `src/peptide_flywheel/prompt_pipeline.py`, `src/peptide_flywheel/ast_repair.py`, `src/peptide_flywheel/circuit_breaker.py`

---

## 1. Executive Summary & Problem Formulation

In multi-agent orchestration systems, unoptimized implementations suffer from three crippling operational bottlenecks:
1. **Context & Token Bloat:** Repeatedly serializing complete target dossiers, hypotheses, and candidate libraries into every prompt packet creates $O(N \times K)$ token bloat and bursts LLM context windows.
2. **KV Cache Busting:** Placing dynamic metadata (timestamps, UUIDs) at the beginning of prompts invalidates LLM KV prompt caching, multiplying inference latency by $3\times–5\times$.
3. **Retry Storms & Cascading Outages:** Unconstrained full-prompt retry loops upon minor schema mismatches exhaust rate limits and compound latency exponentially.

Pillar 4 establishes an SRE-grade agent runtime:
* **Content-Addressed Storage (CAS):** Immutable SHA-256 entity storage (`cas://<sha256>`) and RFC 6902 JSON Patch state deltas.
* **3-Tier Prefix-Invariant Prompts:** Structuring prompt text so $80\%+$ of tokens are permanently KV-cached.
* **Localized AST Repair:** In-place deterministic context normalization and subtree micro-patching without full regenerations.
* **3-State SRE Circuit Breakers:** Graceful degradation to deterministic heuristics with Dead-Letter Queue (DLQ) logging.

---

## 2. Mathematical & Algorithmic Specifications

### 2.1 Content-Addressed Storage (CAS) & RFC 6902 Deltas

```
┌──────────────────────────────────────────────────────────┐
│             MERKLE CONTENT-ADDRESSED STORE               │
└──────────────────────────────────────────────────────────┘
  Target Dossier T    ──► Hash: SHA256(T) ──► cas://e3b0c442...
  Hypothesis H        ──► Hash: SHA256(H) ──► cas://f1a234b8...
  Candidate Card C    ──► Hash: SHA256(C) ──► cas://8c91a03e...

  Agent Prompt Envelope:
  {
    "target_ref": "cas://e3b0c442...",
    "hypothesis_ref": "cas://f1a234b8...",
    "candidate_ref": "cas://8c91a03e...",
    "state_delta": [
      { "op": "add", "path": "/risk_flags/-", "value": "HIGH_HYDROPHOBICITY" }
    ]
  }
```

* **Storage Invariant:** Canonical serialization: $\text{JSONBytes}(x)$ sorted by keys, separators `(',', ':')`.
* **State Mutation:** Pipeline stages emit lightweight RFC 6902 JSON Patch arrays rather than re-transmitting entire candidate objects, reducing inter-agent token bandwidth by **$75\%–90\%$**.

---

### 2.2 3-Tier Prefix-Invariant Prompt Layout for KV Caching

Modern LLM inference engines (vLLM RadixAttention, Anthropic, OpenAI, Gemini) match prompt prefixes against GPU KV-caches. 

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: Static Invariant Prefix (~1,500 tokens) - 100% Permanently Cached│
│ • Agent Persona, System Philosophy, Output Rules, Failure Ontology     │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Semi-Static Campaign Context (~3,000 tokens) - Cached per Target │
│ • Target Dossier, Inclusion/Exclusion Criteria, Standard Assay Controls │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: Volatile Dynamic Tail (~300 tokens) - Uncached Dynamic Input   │
│ • Specific Candidate Sequence, Local Descriptors, Task Instruction    │
└────────────────────────────────────────────────────────────────────────┘
```

**Layout Rule:** Dynamic identifiers (`packet_id`, `run_id`, timestamps, random seeds) are *strictly forbidden* from appearing in Tier 1 or Tier 2.

---

### 2.3 Localized AST Error Repair Engine

When an agent response fails Pydantic schema validation or context-ID verification, executing a full prompt retry compounds latency.

```
Agent Raw JSON Response
         │
         ▼
┌─────────────────────────────────────────┐
│ 1. Deterministic Normalization (0 LLM)  │
│    • Force target_id, hypothesis_id     │
│    • Uppercase amino acid sequence      │
│    • Clamp float scores into [0.0, 1.0] │
└────────────────────┬────────────────────┘
                     │
                     ▼
             Schema Validated?
           ┌─────────┴─────────┐
           ▼ YES               ▼ NO
      [ACCEPT]        ┌───────────────────────────────────┐
                      │ 2. AST Subtree Isolation          │
                      │    Isolate invalid subfield node  │
                      └────────────────┬──────────────────┘
                                       │
                                       ▼
                      ┌───────────────────────────────────┐
                      │ 3. Micro-Prompt Repair (50 tokens)│
                      │    Fix ONLY the isolated subfield │
                      └───────────────────────────────────┘
```

---

### 2.4 3-State SRE Circuit Breaker & Concurrency Bulkheads

```
                  [Agent Task Ingestion]
                             │
                             ▼
              ┌──────────────────────────────┐
              │ State == CLOSED? (Normal)    │
              └──────────────┬───────────────┘
                     YES     │      NO
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────┐          ┌───────────────────────┐
│ Invoke Remote LLM API │          │ Trip to OPEN State:   │
└───────────┬───────────┘          │ Execute Heuristic     │
            │                      │ Fallback (scoring.py) │
       Fail │                      │ & Log to DLQ Journal  │
            ▼                      └───────────────────────┘
[Failure Rate > 40% in 5m Window]
            │
            ▼
[Trip Breaker -> OPEN for 60s Backoff]
```

* **Concurrency Bulkheads:** Thread/coroutine pool isolation prevents a slow external model (e.g. AlphaFold/Structure agent) from starving fast scoring agents.
* **Decorrelated Exponential Backoff with Jitter:**
  $$t_{\text{sleep}} = \text{Uniform}\left(0, \min(t_{\max}, t_{\text{base}} \times 2^{\text{attempt}})\right)$$

---

## 3. Data Structures & Schemas

```python
# src/peptide_flywheel/cas_store.py
from dataclasses import dataclass
from typing import Any
from pathlib import Path

@dataclass
class CompactContextEnvelope:
    packet_id: str
    target_ref: str        # e.g. "cas://e3b0c442..."
    hypothesis_ref: str    # e.g. "cas://f1a234b8..."
    candidate_ref: str     # e.g. "cas://8c91a03e..."
    state_delta: list[dict[str, Any]]  # RFC 6902 JSON Patch
    projection_fields: list[str]

# src/peptide_flywheel/circuit_breaker.py
from enum import Enum

class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: float = 0.40  # 40% failure rate triggers trip
    sliding_window_size: int = 20    # last 20 calls
    recovery_timeout_sec: float = 60.0
```

---

## 4. Implementation Steps & Milestones

1. **`src/peptide_flywheel/cas_store.py`**:
   - Implement `ContentAddressedStore` with SHA-256 keying and local disk backing.
   - Implement `apply_rfc6902_patch(source_obj, delta)` and `compute_rfc6902_diff(obj_a, obj_b)`.
2. **`src/peptide_flywheel/prompt_pipeline.py`**:
   - Refactor prompt templates into Tier 1 (Static System), Tier 2 (Target Context), and Tier 3 (Candidate Tail).
3. **`src/peptide_flywheel/ast_repair.py`**:
   - Implement deterministic normalization layer (`normalize_candidate_card_ast()`).
   - Implement AST subtree isolation and micro-prompt patcher.
4. **`src/peptide_flywheel/circuit_breaker.py`**:
   - Implement `AgentCircuitBreaker` with rolling failure window and half-open state.
   - Implement Dead-Letter Queue (DLQ) persistent disk journal (`.flywheel_dlq/`).

---

## 5. Verification & Test Suite

- `tests/test_cas_store.py`:
  - Test 1: Store Target and Candidate objects; verify retrieval by `cas://` URI produces exact byte match.
  - Test 2: Apply RFC 6902 patch updating candidate status and risk flags; verify correct object state.
- `tests/test_ast_repair.py`:
  - Test 3: Pass candidate payload with missing `target_id`, un-normalized sequence `" acdef "`, and string score `"0.85"`. Verify deterministic normalizer fixes all without LLM invocation.
- `tests/test_circuit_breaker.py`:
  - Test 4: Simulate 10 consecutive API failures; verify breaker trips to `OPEN`, immediately routes subsequent calls to `scoring.heuristic_manufacturability_score`, and logs entries to `.flywheel_dlq/`.
