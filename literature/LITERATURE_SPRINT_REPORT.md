# Literature Sprint Report

## 1) Searches performed

- arXiv antimicrobial peptide machine learning benchmark leakage
- arXiv antimicrobial peptide generation
- arXiv antimicrobial peptide haemolysis prediction
- arXiv antimicrobial peptide toxicity prediction
- Artificial intelligence-driven antimicrobial peptide discovery
- A Standardized Benchmark for Peptide Machine Learning
- Prediction of Hemolysis Tendency of Peptides using a Reliable Evaluation Method
- AmpLyze
- HMAMP
- MoFormer
- PeptideGPT
- PepTune
- Full-Atom Peptide Design with Geometric Latent Diffusion
- DiffPepBuilder
- Zero-Shot Cyclic Peptide Design via Composable Geometric Constraints
- GeoPep
- AutoBinder Agent / MCP-based protein binder design
- MAC-AMP
- surveys on scientific and autonomous agents
- AutoResearchBench
- MCP-Cosmos
- AI Scientist-v2
- Why LLMs Aren't Scientists Yet

## 2) Papers included

- 21 papers were included in the registry and linked into module map.
- Registry IDs: `LIT-AMP-001` to `LIT-AMP-021`.

## 3) Papers rejected

- Non-arXiv or non-verifiable targets without reliable metadata for fields (dataset/method/validation/leakage) in this pass.
- General peptide-manufacturability papers without peptide-specific or arXiv-traceable details.
- Duplicative or low-signal general reviews with no direct pipeline mapping.

## 4) Top 5 must-read papers

1. LIT-AMP-001
2. LIT-AMP-002
3. LIT-AMP-004
4. LIT-AMP-007
5. LIT-AMP-015

## 5) Docs updated

- `literature/arxiv_literature_registry.csv`
- `literature/arxiv_literature_registry.md`
- `literature/module_evidence_map.md`
- `literature/search_log.md`
- `literature/rejected_papers.md`
- `literature/paper_notes/README.md`
- `literature/paper_notes/LIT-AMP-001_pepbenchmark.md` to `literature/paper_notes/LIT-AMP-021_llms_aren_t_scientists_yet.md`
- `literature/LITERATURE_SPRINT_REPORT.md`
- `docs/amp_design_rules.md`
- `docs/amp_inclusion_exclusion_criteria.md`
- `docs/04_failure_ontology.md`
- `docs/05_manufacturability_framework.md`
- `docs/03_agent_specs.md`
- `docs/10_literature_review_plan.md`

## 6) Key implementation lessons

- Start with benchmark-correct data governance (PepBenchmark + ESCAPE style ontology) before model tuning (`LIT-AMP-001`, `LIT-AMP-002`).
- Treat hemolysis and toxicity as first-class constraints, not post-filters (`LIT-AMP-003`, `LIT-AMP-004`, `LIT-AMP-007`).
- Implement multi-objective generation with explicit tradeoff templates and hard safety gates (`LIT-AMP-005`, `LIT-AMP-006`, `LIT-AMP-015`).
- Prioritize cyclic and binder-specific pathways with route-specific feasibility checks (`LIT-AMP-010`, `LIT-AMP-011`, `LIT-AMP-012`).
- Build agent orchestration with explicit uncertainty, reproducibility, and failure taxonomy (`LIT-AMP-014`, `LIT-AMP-019`, `LIT-AMP-021`).

## 7) Warnings for dataset leakage / overclaiming

- Leakage risk remains high when homology-aware splitting is not explicit (`LIT-AMP-003`, `LIT-AMP-001`).
- Do not report numeric gains from abstract-level claims without full-method confirmation (`uncertain` where needed).
- Avoid claiming causal efficacy from literature-agent scores unless backed by wet-lab outcomes.

## 8) What to read manually first

- LIT-AMP-001 (methods + split protocol)
- LIT-AMP-002 (ESCAPE schema + split assumptions)
- LIT-AMP-007 (objective-guided generation implementation details)
- LIT-AMP-014 (agent orchestration contract)
- LIT-AMP-015 (AMP-specific multi-agent control logic)

## 9) Recommended next Codex task

- Next: implement the registry-linked registry IDs in `docs` schema loaders and add a leakage-aware split check in `scripts/` for AMP and hemolysis validation.
