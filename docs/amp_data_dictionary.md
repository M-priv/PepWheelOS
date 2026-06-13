# AMP Data Dictionary

## `data/processed/amp_seed_dataset.csv`

| Field | Type | Required | Description |
|---|---|---|---|
| `peptide_id` | string | yes | Stable peptide identifier used as the primary key across dataset artifacts. |
| `name` | string | yes | Human-readable peptide name, synonyms, and/or clinical code. |
| `sequence` | string | yes | Single-letter amino-acid sequence. |
| `length` | integer | yes | Sequence length in amino acids. |
| `source_database` | string | yes | Source system or systems (e.g., `DBAASP;DRAMP`). |
| `source_organism` | string | yes | Producer or source organism/context. |
| `target_microbe` | string | yes | Target organism used for the curated activity row. |
| `gram_status` | string | yes | `Gram-positive`, `Gram-negative`, `Gram+/Gram-`, `Fungal`, or `Unknown`. |
| `activity_type` | string | yes | Activity readout type (e.g., `MIC`, `IC50`). |
| `mic_value` | string | yes | Reported potency value(s). Keep as string for ranges and inequality operators. |
| `mic_unit` | string | yes | Unit string used in `mic_value` (e.g., `µg/ml`, `µM`, `microM`). |
| `assay_conditions` | string | no | Minimal context for assay method/medium. |
| `haemolysis_value` | string | no | Reported hemolysis values and context (if available). |
| `cytotoxicity_value` | string | no | Reported cytotoxicity values and context (if available). |
| `modifications` | string | yes | Known modifications, modifications state, or `none`. |
| `linear_or_cyclic` | string | yes | `linear` or `cyclic`. |
| `net_charge` | string/integer | no | Net charge if reported or pre-computed. |
| `hydrophobic_fraction` | string/float | no | Fraction hydrophobic residues (precomputed if available). |
| `aromatic_count` | integer | no | Number of aromatic residues in sequence. |
| `cysteine_count` | integer | no | Number of `C` residues. |
| `methionine_count` | integer | no | Number of `M` residues. |
| `asparagine_glutamine_count` | integer | no | Number of `N` + `Q` residues. |
| `known_stability_notes` | string | no | Literature or curation notes on stability liabilities. |
| `known_solubility_notes` | string | no | Literature or curation notes on solubility/manufacturing concerns. |
| `reference` | string | yes | Source reference key or URL. |
| `notes` | string | no | Curation rationale, bucket alignment, or additional risk context. |

## `data/processed/amp_liability_examples.csv`

| Field | Type | Required | Description |
|---|---|---|---|
| `peptide_id` | string | yes | Identifier matching seed table entries where applicable. |
| `name` | string | yes | Peptide label and aliases. |
| `source_database` | string | yes | Primary source system for the liability observation. |
| `source_organism` | string | yes | Source organism/context. |
| `liability_bucket` | string | yes | Curation bucket (`liability` or `near-negative`). |
| `liability_type` | string | yes | Liability class (e.g., `cytotoxicity`, `weak_potency`, `translational`). |
| `sequence` | string | yes | Sequence associated with the liability example. |
| `target_organism` | string | yes | Target used for reported liability statement. |
| `severity` | string | yes | `low`, `medium`, or `high`. |
| `metric` | string | yes | Quantified liability value/range. |
| `reference` | string | yes | Source reference key or URL. |
| `notes` | string | no | Short interpretation statement for scoring.

## Literature-linked implementation notes

- Keep raw fields (`mic_unit`, `reference`, `notes`) as low-friction provenance anchors for leakage and ontology checks (`LIT-AMP-001`, `LIT-AMP-002`).
- Add `validation_split_tag` or equivalent provenance column in downstream transforms to capture similarity-aware or homology-aware split strategy (`LIT-AMP-003`, `LIT-AMP-018`).
- For cyclic candidates, explicitly model `cyclisation_mode` and `ring_strategy` in feature pipelines before manufacturability scoring (`LIT-AMP-012`).
- Record uncertainty when fields are inferred from abstracts only or non-standard assays (`LIT-AMP-009` marked as uncertain).
