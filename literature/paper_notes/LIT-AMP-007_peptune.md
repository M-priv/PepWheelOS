# PepTune: De Novo Generation of Therapeutic Peptides with Multi-Objective-Guided Discrete Diffusion

## Metadata

Title: PepTune: De Novo Generation of Therapeutic Peptides with Multi-Objective-Guided Discrete Diffusion
Authors: Sophia Tang; Yinuo Zhang; Pranam Chatterjee
Year: 2024
arXiv ID: 2412.17780
URL: https://arxiv.org/abs/2412.17780
Module tags: module_5,module_4,module_6,module_8
Priority: must_read_now

## Summary

PepTune uses discrete diffusion with multi-objective guidance (including toxicity and solubility signals) and appears to be one of the strongest current examples for closed-loop peptide proposal generation in your stack.

## Why this matters for the peptide flywheel

It matches your need to generate candidates with explicit trade-offs and can feed directly into red-team and manufacturing filters.

## Dataset used

Therapeutic peptide corpora with property labels and reward models; exact corpus list needs manual confirmation.

## Method/model

Discrete diffusion with MCTG (multi-constraint guidance + exploration/exploitation control).

## Validation design

Comparative generation quality and objective satisfaction against baselines.

## Leakage or bias risks

Objective reward leakage and label imbalance can collapse exploration; maintain held-out objective distributions.

## Toxicity/haemolysis relevance

Core relevance for multi-property filtering.

## Manufacturability relevance

Medium-high: supports non-toxic and property-friendly sampling before synthesis scheduling.

## Agentic workflow relevance

High as a callable generator node with objective contract.

## Limitations

Full text needed for exact hyperparameters and cost profile.

## What to implement

- Pilot PepTune-like objective scheduling: safety-first, then potency.
- Add explicit novelty penalties to reduce near-duplicate generation.

## What to avoid

- Do not permit unconstrained latent steps without post-generation chemical sanity checks.

## Questions I should manually review

- What objective weights were robust across protein classes?
- How much filtering was needed post-sampling?
