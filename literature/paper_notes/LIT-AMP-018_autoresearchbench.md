# AutoResearchBench: Benchmarking AI Agents on Complex Scientific Literature Discovery

## Metadata

Title: AutoResearchBench: Benchmarking AI Agents on Complex Scientific Literature Discovery
Authors: Lei Xiong et al.
Year: 2026
arXiv ID: 2604.25256
URL: https://arxiv.org/abs/2604.25256
Module tags: module_8,module_3,module_2
Priority: useful_next

## Summary

This benchmark evaluates AI agents on complex scientific literature tasks and introduces Deep Research and Wide Research modes with measurable quality and failure signals.

## Why this matters for the peptide flywheel

Ideal for validating your literature-agent before it informs design rules, preventing over-claiming from noisy text mining.

## Dataset used

Curated benchmark query/task set for scientific literature extraction.

## Method/model

Agent framework benchmark across literature discovery tasks.

## Validation design

Task scoring by correctness, coverage, and chain-of-thought quality.

## Leakage or bias risks

Benchmark contamination is possible if models are fine-tuned on task prompts; still useful as relative indicator.

## Toxicity/haemolysis relevance

Indirect.

## Manufacturability relevance

Indirect.

## Agentic workflow relevance

High for literature ingestion quality assurance and source citation checks.

## Limitations

Does not measure wet-lab outcomes or generation fidelity.

## What to implement

- Use a thin, repeatable protocol for literature-agent regression tests.
- Reject unsupported claims unless confidence + citation checks pass.

## What to avoid

- Do not use paper score as a direct proxy for experimental success.

## Questions I should manually review

- Are benchmark prompts similar to your real protocol language?
- Which failure types mirror your domain most closely?
