# Roadmap

## Phase 0: Scaffold and domain setup

Goal:
Create a clean structure for the system and define schemas before writing complex code.

Deliverables:
- Research object schemas
- Candidate card schema
- Failure ontology
- Agent protocols
- Example campaign folder
- Manual data-entry workflow

## Phase 1: Manual flywheel

Goal:
Make the system useful even before automation.

Deliverables:
- Manually populated target dossier
- 10 to 30 peptide candidate cards
- Manufacturability scores
- Red-team critiques
- Assay plan
- Simulated results and failure classification

## Phase 2: Semi-automated agents

Goal:
Use LLMs to populate structured records, but keep humans in control.

Deliverables:
- Target dossier generation prompt
- Candidate-card generation prompt
- Red-team prompt
- Assay-pack generation prompt
- Structured JSON output validation

## Phase 3: Scientific tooling integration

Goal:
Connect specialist tools and models.

Potential integrations:
- RDKit or Biopython for molecular/sequence descriptors
- Protein language model embeddings
- Structure prediction outputs
- Docking or structural scoring workflows
- Molecular dynamics analysis outputs
- Toxicity, solubility and aggregation predictors

## Phase 4: Experimental feedback loop

Goal:
Ingest CRO/CDMO and assay outputs into the research graph.

Deliverables:
- Synthesis result parser
- Assay result schema
- Failure taxonomy mapping
- Next-round design recommendation engine

## Phase 5: Portfolio and venture demo

Goal:
Show a complete end-to-end campaign.

Deliverables:
- One public demo campaign with safe/non-sensitive target
- Technical report
- Architecture diagram
- Investor-readable summary
- GitHub repo with reproducible examples
