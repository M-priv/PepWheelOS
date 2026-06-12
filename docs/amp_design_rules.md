# AMP Seed Dataset Design Rules (Manufacturability Aware)

## Scope

- `amp_seed_dataset.csv` holds the curated curation-ready candidate table.
- `amp_liability_examples.csv` holds explicit liability examples used by review scoring and red-team checks.
- `scripts/validate_amp_dataset.py`, `scripts/calculate_amp_features.py`, and `scripts/generate_candidate_cards_from_csv.py` operate on this schema.

## Schema requirements for `amp_seed_dataset.csv`

1. The following columns are required (exact names):
   - `peptide_id`
   - `name`
   - `sequence`
   - `length`
   - `source_database`
   - `source_organism`
   - `target_microbe`
   - `gram_status`
   - `activity_type`
   - `mic_value`
   - `mic_unit`
   - `assay_conditions`
   - `haemolysis_value`
   - `cytotoxicity_value`
   - `modifications`
   - `linear_or_cyclic`
   - `net_charge`
   - `hydrophobic_fraction`
   - `aromatic_count`
   - `cysteine_count`
   - `methionine_count`
   - `asparagine_glutamine_count`
   - `known_stability_notes`
   - `known_solubility_notes`
   - `reference`
   - `notes`

2. `peptide_id` must be unique.
3. `length` must match `len(sequence)` when present.
4. `sequence` should be uppercase single-letter amino acids.
5. `linear_or_cyclic` should be `linear` or `cyclic`.
6. `gram_status` should be one of `Gram-positive`, `Gram-negative`, `Gram+/Gram-`, `Fungal`, or `Unknown`.

## Manufacturability-focused curation gates

1. Flag and deprioritise sequences with:
   - very high aromatic burden (`aromatic_count > 8`)
   - high hydrophobicity (`hydrophobic_fraction > 0.6`) unless formulation evidence is strong
   - many disulfides (`cysteine_count >= 4`) without clear synthetic rationale
   - short, highly hydrophobic fragments without clear support in stability notes
2. Prefer low `asparagine_glutamine_count` for long campaigns unless rapid synthesis control is available.
3. Capture formulation context directly in `known_stability_notes` and `known_solubility_notes`.
4. Include explicit clinical or assay failure context in `notes` to support manufacturability-aware scoring.

## `amp_liability_examples.csv`

Required columns:
- `peptide_id`
- `name`
- `source_database`
- `source_organism`
- `liability_bucket`
- `liability_type`
- `sequence`
- `target_organism`
- `severity`
- `metric`
- `reference`
- `notes`

`severity` values: `low`, `medium`, `high`.

## Review workflow

1. Populate and review `amp_seed_dataset.csv` from public source pulls.
2. Populate `amp_liability_examples.csv` with explicit negative patterns.
3. Run `scripts/validate_amp_dataset.py --seed data/processed/amp_seed_dataset.csv --liability data/processed/amp_liability_examples.csv`.
4. Run `scripts/calculate_amp_features.py` to normalize computed features.
5. Generate cards with `scripts/generate_candidate_cards_from_csv.py`.
