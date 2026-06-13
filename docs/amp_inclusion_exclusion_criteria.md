# AMP Inclusion / Exclusion Criteria

## Inclusion (must-have)

1. Valid peptide sequence and deterministic length (`sequence` + `length` consistency).
2. Source traceability with stable identifier and assay context (`reference` + `assay_conditions`).
3. Clear activity label mapping using ESCAPE-like hierarchy (`antimicrobial`, `fungal`, `viral`, `toxic`) where available (`LIT-AMP-002`).
4. Hemolysis/toxicity fields present if measured or explicitly marked missing (`LIT-AMP-003`, `LIT-AMP-004`).
5. At least one non-ambiguous split/validation policy attached before training (`LIT-AMP-001`).
6. Cyclic candidates include ring/constraint notes and cyclization strategy (`LIT-AMP-012`).

## Exclusion (hard)

1. Sequence anomalies (non-standard residues not justified in `modifications`).
2. Contradictory or unverifiable assay units across `mic_value`/`mic_unit`.
3. No experimental toxicity context when target program requires safety-first cohorts (`LIT-AMP-004`, `LIT-AMP-008`).
4. Duplicate or near-duplicate sequences across splits without split-safe dedup metadata (`LIT-AMP-003`, `LIT-AMP-001`).
5. Unknown or unavailable provenance for labels (unless manually reviewed).

## Uncertain/investigative items (needs_manual_review)

- Papers or rows from external corpora with unresolved harmonization decisions.
- Any full-text-only claims not reproducible from abstract-level metadata in this sprint.

## Inclusion gating notes

- Inclusion is conservative by default for early rounds.
- Any candidate passing safety gates but failing manufacturability gates gets `status: revise` first, not auto-excluded.
- Keep all uncertain rows under a separate review bucket rather than hard deleting.
