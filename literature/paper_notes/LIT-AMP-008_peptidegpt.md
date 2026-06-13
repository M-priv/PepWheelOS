# Peptide-GPT: Generative Design of Peptides using Generative Pre-trained Transformers and Bio-informatic Supervision

## Metadata

Title: Peptide-GPT: Generative Design of Peptides using Generative Pre-trained Transformers and Bio-informatic Supervision
Authors: Aayush Shah; Chakradhar Guntuboina; Amir Barati Farimani
Year: 2024
arXiv ID: 2410.19222
URL: https://arxiv.org/abs/2410.19222
Module tags: module_5,module_4,module_6,module_8
Priority: useful_now

## Summary

Peptide-GPT demonstrates a practical generation loop where LLM-generated sequences are filtered by perplexity, geometry checks, ESMFold structure validity, and task-specific bioinformatic classifiers.

## Why this matters for the peptide flywheel

This is closest to a productionizable generation gate stack and can be adapted with your safety/manufacturability models.

## Dataset used

Curated peptide datasets for antimicrobial/biological tasks; exact corpus details need full-text verification.

## Method/model

GPT-like sequence generator with multi-stage filtering and property-specific binary models.

## Validation design

Perplexity, in-silico filtering rates, and downstream task model performance.

## Leakage or bias risks

As with any LLM pretrain/fine-tune path, hidden overlap across curated datasets can inflate generation quality scores.

## Toxicity/haemolysis relevance

Has explicit non-fouling and hemolysis-relevant checkpoints.

## Manufacturability relevance

Useful with structure filtering and property classifier stack.

## Agentic workflow relevance

High: maps cleanly to orchestrated pipeline tasks with deterministic checkpoints.

## Limitations

Full split strategies and dataset harmonization are not fully inferable from abstract alone.

## What to implement

- Add staged validation gates: language validity, folding plausibility, toxicity predictor gating.
- Enforce deterministic seed and audit hash per run.

## What to avoid

- Don’t rely on perplexity as a safety proxy.

## Questions I should manually review

- How much filtering reduces mode collapse?
- What is failure recovery logic when structure checks reject most samples?
