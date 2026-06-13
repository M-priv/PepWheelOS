# AutoBinder Agent: An MCP-Based Agent for End-to-End Protein Binder Design

## Metadata

Title: AutoBinder Agent: An MCP-Based Agent for End-to-End Protein Binder Design
Authors: Fukang Ge; Jiarui Zhu; Linjie Zhang; Haowen Xiao; Xiangcheng Bao; Fangnan Xie; Danyang Chen; Yanrui Lu; Yuting Wang; Ziqian Guan; Lin Gu; Jinhao Bi; Yingying Zhu
Year: 2026
URL: https://arxiv.org/abs/2602.00019
arXiv ID: 2602.00019
Module tags: module_8,module_6,module_9
Priority: must_read_now

## Summary

AutoBinder presents a working MCP-based scientific agent stack that orchestrates prediction, generative design, structure tools, and scoring with explicit tool-calling workflows for protein binders.

## Why this matters for the peptide flywheel

It is the closest direct template for your desired agent architecture and offers practical orchestration patterns.

## Dataset used

Not primarily dataset-centric; focuses on workflow and tool integration.

## Method/model

LLM planner + MCP tool graph with modules for structure prediction/refinement and scoring.

## Validation design

Architecture-level evaluation against baseline/manual workflows and end-to-end task completion.

## Leakage or bias risks

Tool-call hallucinations and stale-cached external tool outputs can bias score-based decisions.

## Toxicity/haemolysis relevance

Indirect via integration; no direct hemolysis model.

## Manufacturability relevance

High because tool orchestration can include synthesis feasibility checks as mandatory checkpoints.

## Agentic workflow relevance

Core. Strongly relevant for docs/agent specs and orchestration interfaces.

## Limitations

Success depends on external tool quality and stable MCP endpoints.

## What to implement

- Mirror tool contract and checkpointing structure.
- Enforce idempotent task steps and artifact logs.

## What to avoid

- Do not auto-accept tool outputs without confidence + provenance checks.

## Questions I should manually review

- Which tool calls fail most under load?
- How is error recovery prioritized versus exploration?
