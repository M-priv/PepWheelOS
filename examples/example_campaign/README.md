# Example Campaign

This folder contains a concrete, reproducible manual-flywheel campaign scaffold.

## Structure

- `target_dossier.md`: populated target dossier for a peptide benchmark context.
- `hypothesis.md`: concrete campaign hypothesis derived from the dossier.
- `target.json` and `hypothesis.json` are included for direct manual script execution.
- `candidates/`: candidate cards (20 cards from the AMP seed dataset).
- `cro/`: CRO request packs for selected candidates.
- `red_team/`: red-team critique reviews for selected candidates.
- `results/`: simulation placeholders and future assay reports.

## How to use

Use `scripts/run_manual_flywheel_round.py` with the target/hypothesis JSON loaded from your own generated JSON files when transitioning from markdown planning to scoring runs.

Run `scripts/run_simulated_result_ingestion.py` against files in `results/` to parse simulated assay outputs and infer failure modes against the ontology.

Close the loop with:

```bash
python scripts/run_result_review.py \
  --candidate-records-dir data/results/manual_round/records \
  --base-dag-json data/results/manual_round/research_graph.json \
  --campaign-id CAMPAIGN-EXAMPLE \
  --run-id REVIEW-001 \
  --result examples/example_campaign/results/simulated_result_AMP_SRC_DBAASP_1001.md \
  --result examples/example_campaign/results/simulated_result_AMP_SRC_DBAASP_690.md \
  --result examples/example_campaign/results/simulated_result_AMP_SRC_DBAASP_1004.md \
  --result examples/example_campaign/results/simulated_result_AMP_SRC_DBAASP_1011.md
```

The run writes `closed_loop_recommendations.json` under `--output-dir` with per-candidate follow-up actions, plus:
- `campaign_recommendation_plan.json`: campaign-wide next-step synthesis/design priorities.
- `next_round_plan.json`: bucketed next-round action list.
- `campaign_decision.json`: campaign-level close-loop decision record (`proceed_to_next_round`, `rework_pool`, or `pause`).
