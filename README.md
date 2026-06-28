# Manufacturability-Aware Peptide Discovery Flywheel

This repository is a scaffold for building an agentic research system for peptide discovery. It is designed around a flywheel philosophy: every target, hypothesis, model run, candidate peptide, synthesis result, assay result, failure mode and next-design decision becomes structured, reusable research memory.

The system is not intended to be a standalone peptide generator. It is intended to become a research operating system around specialist models, human expert review, CRO/CDMO workflows and eventually wet-lab feedback.

## Core thesis

Most AI peptide tools over-emphasise candidate generation. A stronger company wedge is:

**LLM-orchestrated, manufacturability-aware peptide discovery with structured experimental feedback loops.**

The defensible asset is not the first model. The defensible asset is the cumulative graph of design decisions, failed syntheses, assay results, manufacturability liabilities and model errors.

## What this scaffold contains

- Research DAG structure
- Target dossier templates
- Peptide candidate card templates
- Agent specifications
- Failure ontology
- Manufacturability scoring framework
- Assay and CRO/CDMO pack templates
- Data schemas
- Python stubs for future implementation
- Active-learning simulation artifacts for next-batch prioritisation
- Planning docs: [roadmap](docs/planning/roadmap.md), [project map](docs/planning/project_map.md), [Codex plugin spec](docs/planning/codex_plugin_spec.md), and [project backlog](backlog/project_backlog.md)
- Documentation for IP, quality, validation and portfolio development

## Suggested build path

The scaffold now supports the first end-to-end loop:

1. Target dossier agent
2. Peptide candidate card system
3. Manufacturability scoring engine
4. Failure ontology
5. Active-learning loop simulator
6. One end-to-end campaign demo

Avoid starting with GMP manufacturing, autonomous wet-lab execution, or training a foundation model.

## Safety and scope

This scaffold is for computational research organisation, hypothesis management, candidate tracking and high-level validation planning. It does not provide wet-lab protocols, manufacturing instructions or clinical claims. Experimental and regulated work should be performed by qualified professionals under appropriate institutional, legal and quality systems.
