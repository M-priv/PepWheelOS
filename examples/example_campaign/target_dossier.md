# Target Dossier

## Target

Name: Antimicrobial Peptide Discovery Sandbox Target
Aliases: AMP-TARGET-001, Sandbox AMP
Organism: Gram-positive and Gram-negative bacterial panels
UniProt ID: Not applicable (pathogen-agnostic screening target set)
PDB IDs: Not applicable

## Use case

Benchmark-style discovery and decision workflow for early-stage antimicrobial peptide candidate curation.

## Biological rationale

This target represents a screening context for broad-spectrum antibacterial peptides with measurable minimal inhibitory concentration (MIC) workflows across shared Gram-positive and Gram-negative strains. The objective is to validate the flywheel workflow with real, publicly available peptide records and keep discovery decisions reproducible.

## Design opportunity

Use known antimicrobial sequence scaffolds to quickly generate and score shortlisted candidates, then track manufacturability risk, toxicity context, and next-action decisions through the structured pipeline.

## Main hypothesis

A curated set of candidate peptides with prior antibacterial signal can be reprioritized using structured manufacturability and governance checks to produce a reproducible shortlist for downstream design and experimental planning.

## Risks

- Data quality and reporting heterogeneity across source databases.
- Strong antibacterial potency may still conflict with developability or safety constraints.
- Dataset-level split metadata is currently incomplete and should be versioned with manifest-level provenance.

## Next action

Score candidate subset with the manual workflow, attach red-team critique artifacts, and add simulated assay readouts for a closed review loop.
