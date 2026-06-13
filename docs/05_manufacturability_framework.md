# Manufacturability Framework

## Aim

Score peptide candidates before synthesis so that the system does not merely optimise predicted binding.

## V0 scoring dimensions

1. Sequence length
2. Net charge
3. Hydrophobicity
4. Aromatic residue burden
5. Cysteine and disulfide complexity
6. Methionine oxidation risk
7. Asparagine/glutamine deamidation risk
8. Aggregation risk
9. Solubility risk
10. Modification complexity
11. Cyclisation complexity
12. Purification risk
13. Cost-of-goods risk

## Literature-informed additions

- Add separate safety-override dimensions for hemolysis/toxicity probability (`LIT-AMP-004`, `LIT-AMP-007`, `LIT-AMP-008`).
- Add cyclic-route risk where ring-closure constraints fail or are unsupported (`LIT-AMP-012`).
- Add synthesis/tool orchestration readiness for MCP-bound workflows (`LIT-AMP-014`, `LIT-AMP-019`).
- Track failure entropy: uncertainty and contradiction count per candidate (`LIT-AMP-021`).

## Output

Each candidate receives:

- Dimension-level scores
- Overall manufacturability score
- Human-readable risk notes
- Suggested mitigation
- Whether to reject, revise, or test

## Important

V0 can be heuristic. The score becomes more valuable after experimental outcomes are ingested.

## Implementation notes

- Use weighted dimensions with configurable profiles (`AMP`, `binder`, `cyclic`).
- Flag candidates exceeding soft thresholds but still allow manual override with justification.
- Store score rationale with provenance for later learning updates.
