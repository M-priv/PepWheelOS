# PepBenchmark: A Standardized Benchmark for Peptide Machine Learning

## Metadata

Title: PepBenchmark: A Standardized Benchmark for Peptide Machine Learning
Authors: Jiahui Zhang; Rouyi Wang; Kuangqi Zhou; Tianshu Xiao; Lingyan Zhu; Yaosen Min; Yang Wang
Year: 2026
arXiv ID: 2604.10531
URL: https://arxiv.org/abs/2604.10531
Module tags: module_1,module_2,module_3,module_5,module_8
Priority: must_read_now

## Summary

PepBenchmark proposes a consolidated peptide ML benchmark stack (29 canonical and 6 non-canonical datasets, data preprocessing templates, and standardized splits/evaluation protocol) to reduce duplicated ad-hoc preprocessing and improve reproducibility of antimicrobial and related peptide tasks.

## Why this matters for the peptide flywheel

It gives a first-principles baseline for dataset ingestion and validation so seed-data workflows use consistent representations, making downstream leakage checks and model comparisons meaningful.

## Dataset used

PepBenchData family dataset bundles with canonical/non-canonical splits, and standardized tasks over multiple peptide domains.

## Method/model

Benchmark protocol design with multiple baseline families: descriptors/classifiers/transfomers and explicit train-validation-test conventions.

## Validation design

Comparative leaderboard-style validation with predefined tasks, clean split definitions, and consistent metric reporting to detect benchmark drift.

## Leakage or bias risks

Leakage risk reduces if split rules are followed, but residual risk remains if external curation metadata is reused without provenance checks; manual review needed for exact split scripts.

## Toxicity/haemolysis relevance

Indirect but provides the evaluation scaffolding that should be applied to toxicity/haemolysis splits to avoid inflated claims.

## Manufacturability relevance

No direct synthesis model, but enables stable model selection that can be upstream to manufacturability scorers.

## Agentic workflow relevance

Useful reference architecture for automated dataset QA agents and leaderboard-driven model arbitration.

## Limitations

Preprint snapshot and benchmark implementation details may evolve; must verify released scripts before locking pipelines.

## What to implement

- Implement schema-aligned dataset ingest using PepBenchmark-style split templates.
- Record split hash, source version, and filter flags in audit logs.

## What to avoid

- Do not mix datasets from different benchmark versions without harmonizing unit/reporting standards.

## Questions I should manually review

- Which exact tasks/splits align with your antimicrobial curation scope?
- Are synthetic peptides and modified residues handled consistently across all folds?
