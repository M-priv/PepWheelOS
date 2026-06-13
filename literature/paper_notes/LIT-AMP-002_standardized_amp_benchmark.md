# A Standardized Benchmark for Multilabel Antimicrobial Peptide Classification

## Metadata

Title: A Standardized Benchmark for Multilabel Antimicrobial Peptide Classification
Authors: Sebastian Ojeda et al.
Year: 2025
arXiv ID: 2511.04814
URL: https://arxiv.org/abs/2511.04814
Module tags: module_1,module_2,module_3,module_5
Priority: must_read_now

## Summary

This paper introduces the ESCAPE corpus (80k peptides from 27 repositories) and a hierarchical multi-label framework for antimicrobial activity dimensions, aiming to replace fragmented AMP curation with cleaner ontology-driven splits.

## Why this matters for the peptide flywheel

It directly supports your seed-data blueprint by aligning activity labels and creating reusable ontology edges for inclusion/exclusion and dataset balancing.

## Dataset used

ESCAPE dataset and mapped legacy antimicrobial repositories.

## Method/model

Multilabel pretraining and evaluation; hierarchical label encoding across organism/pathogen/assay variants.

## Validation design

Comparative benchmark setup with standardized metrics and multiple baseline families for anti-microbial classification.

## Leakage or bias risks

Label conflict across repositories and repeated homologs remain major leakage vectors unless de-duplicated with sequence-aware blocking.

## Toxicity/haemolysis relevance

Moderate; toxicity labels are secondary but useful for aligning negative outcome tagging.

## Manufacturability relevance

Not direct, but taxonomy quality improves failure ontology and exclusion precision.

## Agentic workflow relevance

Useful for automatic ontology sync and rule-generation agents.

## Limitations

Full negative set creation and split scripts are needed from full text for exact reproducibility.

## What to implement

- Replace current loose activity fields with hierarchical labels from this paper where possible.
- Add an inclusion rule that rejects labels with unresolved mapping.

## What to avoid

- Avoid treating curated repository labels as ground truth without conflict resolution checks.

## Questions I should manually review

- What is the exact label harmonization policy for MIC vs inhibition/zone assays?
- Are organism taxonomies preserved at species or gram group level?
