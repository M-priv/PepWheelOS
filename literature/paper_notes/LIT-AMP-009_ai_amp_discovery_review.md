# Artificial intelligence-driven antimicrobial peptide discovery

## Metadata

Title: Artificial intelligence-driven antimicrobial peptide discovery
Authors: Paulina Szymczak; Ewa Szczurek
Year: 2023
arXiv ID: 2308.10921
URL: https://arxiv.org/abs/2308.10921
Module tags: module_1,module_8,module_5,module_4
Priority: useful_now

## Summary

This review maps historical and recent AI approaches for AMP classification, generation, and property prediction, and highlights practical pitfalls around data imbalance, validation, and trust in generated sequences.

## Why this matters for the peptide flywheel

Good for module onboarding and for reducing duplicated mistakes in current workflow design.

## Dataset used

Literature-level survey across multiple datasets, not a single benchmark source.

## Method/model

Review and taxonomy paper summarizing GAN/transformer/classical methods and prediction paradigms.

## Validation design

N/A synthetic synthesis evaluation; compares reported validation strategies across studies.

## Leakage or bias risks

Inherent review-level bias toward highly-cited baselines; use as secondary signal only.

## Toxicity/haemolysis relevance

Moderate.

## Manufacturability relevance

Low direct, but useful for understanding typical deployment pitfalls.

## Agentic workflow relevance

Medium through strategic workflow suggestions.

## Limitations

Not a primary benchmarking source.

## What to implement

- Use review taxonomy to define module boundaries and metric standards.
- Encode recommended controls as explicit SOP checks.

## What to avoid

- Avoid using this as a direct benchmark citation for numeric claims.

## Questions I should manually review

- Which cited datasets now have known leakage problems?
- Which methods fail on cyclic or modified peptides?
