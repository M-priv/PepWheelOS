# System Architecture

## High-level architecture

User or scientist
↓
Campaign workspace
↓
Research DAG
↓
Agent layer
↓
Specialist tools and models
↓
Candidate cards
↓
Experimental feedback
↓
Next design round

## Core storage objects

- Target
- Hypothesis
- DesignBatch
- PeptideCandidate
- PredictionRun
- ManufacturabilityAssessment
- AssayPlan
- CRORequest
- ExperimentalResult
- FailureMode
- DecisionRecord
- NextDesignRecommendation

## Agent layer

Each agent should read and write structured objects. Avoid agents that only produce prose.

Agents:

- Target Intelligence Agent
- Design Orchestrator Agent
- Candidate Card Agent
- Manufacturability Agent
- Structure Agent
- Red-Team Agent
- Assay Planning Agent
- CRO/CDMO Pack Agent
- Learning Agent
- Report Agent

## Recommended implementation stack

V0:
- Python
- Pydantic
- SQLite or JSONL
- NetworkX
- Markdown reports
- Local file system

V1:
- Postgres
- Graph database if needed
- Web UI
- Queue-based tool execution
- Model registry
- Audit log

V2:
- External model integrations
- CRO result ingestion
- Active learning
- User permissions
- Versioned research artefacts
