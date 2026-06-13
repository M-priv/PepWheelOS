# GeoPep: A geometry-aware masked language model for protein-peptide binding site prediction

## Metadata

Title: GeoPep: A geometry-aware masked language model for protein-peptide binding site prediction
Authors: Dian Chen; Yunkai Chen; Tong Lin; Sijie Chen; Xiaolin Cheng
Year: 2025
arXiv ID: 2510.27040
URL: https://arxiv.org/abs/2510.27040
Module tags: module_9,module_8,module_1
Priority: useful_next

## Summary

GeoPep presents a geometry-aware transfer strategy from ESM3 to protein-peptide binding-site prediction in sparse-data regimes, improving site inference with minimal peptide examples.

## Why this matters for the peptide flywheel

Helps the target intelligence/binder routing step by preselecting feasible and specific protein surfaces before generator spending.

## Dataset used

Protein-peptide structural-site datasets with sparse annotations.

## Method/model

Geometry-conditioned masked language modeling and transfer learning.

## Validation design

Site prediction accuracy and generalization on held-out sparse site examples.

## Leakage or bias risks

Site-overlap leakage in sparse families likely if strict family splits are not enforced.

## Toxicity/haemolysis relevance

No direct toxicity model.

## Manufacturability relevance

Indirect; reduces futile binder attempts at unreachable sites.

## Agentic workflow relevance

Useful as an upstream filtering agent step.

## Limitations

Limited structural coverage may reduce performance on novel targets.

## What to implement

- Add GeoPep-like site candidates into `target site` evidence used by design agent.
- Require confidence thresholds before passing to binder generator.

## What to avoid

- Avoid single-site commits from low-confidence predictions.

## Questions I should manually review

- How does binding-site calibration shift by target family?
- What fallback exists for low-coverage proteins?
