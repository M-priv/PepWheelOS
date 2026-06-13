# Example Campaign

This folder contains a concrete, reproducible manual-flywheel campaign scaffold.

## Structure

- `target_dossier.md`: populated target dossier for a peptide benchmark context.
- `hypothesis.md`: concrete campaign hypothesis derived from the dossier.
- `target.json` and `hypothesis.json` are included for direct manual script execution.
- `candidates/`: candidate cards (20 cards from the AMP seed dataset).
- `results/`: simulation placeholders and future assay reports.

## How to use

Use `scripts/run_manual_flywheel_round.py` with the target/hypothesis JSON loaded from your own generated JSON files when transitioning from markdown planning to scoring runs.

## Next expansion

- Add manual red-team and CRO synthesis pack files.
- Add a campaign-level decision record after one scoring round.
