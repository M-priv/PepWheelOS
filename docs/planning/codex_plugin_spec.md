# Codex Plugin Spec

## Purpose

Define a future Codex plugin or skill that operates exclusively inside this repository as an agentic operator for the Peptide Discovery Flywheel scaffold.

The plugin is not the scientific system. The plugin is the operating layer that helps an agent inspect the repo, run the right scripts, validate artifacts, summarize campaign state, and recommend the next build or campaign action.

## Repository Scope

The plugin should only run when the current workspace looks like this repo.

Required repo markers:
- `src/peptide_flywheel/`
- `schemas/`
- `scripts/run_manual_flywheel_round.py`
- `scripts/build_prompt_batch.py`
- `scripts/run_result_review.py`
- `scripts/run_active_learning_simulator.py`
- `docs/planning/roadmap.md`

If these markers are missing, the plugin should refuse to operate and explain that it is scoped to the Peptide Discovery Flywheel scaffold repository.

## Boundary

Core system responsibilities remain in this repo:
- Pydantic models and schemas
- Artifact validation
- Manual flywheel execution
- Prompt packet generation
- Result ingestion and review
- Active-learning simulation
- Research DAG persistence
- Reports and campaign artifacts
- Tests

Plugin responsibilities:
- Decide which existing workflow to run
- Inspect campaign state
- Validate required inputs before running commands
- Explain generated artifacts
- Recommend the next repo action
- Maintain safety and scope boundaries

The plugin must not:
- Invent wet-lab protocols
- Make clinical or efficacy claims
- Bypass artifact validation
- Mutate scientific records without leaving a structured artifact trail
- Treat heuristic scores as trained model predictions

## First Version Shape

Start as a Codex skill before building a fuller plugin.

Suggested package shape:

```text
peptide-flywheel-agent/
  SKILL.md
  references/
    workflow_recipes.md
    artifact_contracts.md
    campaign_state_checklist.md
    safety_scope.md
```

The first version should be instruction-heavy and tool-light. It should rely on the repo's existing scripts instead of duplicating logic.

## Named Workflows

### assess_repo_state

Purpose:
Summarize branch state, dirty files, available campaign artifacts, latest generated outputs, and likely next action.

Inputs:
- Current working directory
- Optional campaign directory

Expected behavior:
- Confirm repo markers are present
- Read planning docs and campaign outputs
- Report dirty/untracked files
- Identify latest manual round, prompt batch, result review, and active-learning artifacts
- Recommend one next command or build item

### run_manual_round

Purpose:
Run the structured manual flywheel scoring workflow.

Primary command:

```bash
PYTHONPATH=src python scripts/run_manual_flywheel_round.py \
  --target-json examples/example_campaign/target.json \
  --hypothesis-json examples/example_campaign/hypothesis.json \
  --candidates-json path/to/candidates.json \
  --campaign-id CAMP-001 \
  --run-id RUN-001 \
  --output-dir data/results/manual_round
```

Expected artifacts:
- `records/*.json`
- `candidate_events.jsonl`
- `prediction_events.jsonl`
- `assessment_events.jsonl`
- `research_graph.json`
- `round_report.md`

### build_prompt_batch

Purpose:
Generate prompt packets for target dossier, candidate-card, red-team, and assay-pack agents.

Primary command:

```bash
PYTHONPATH=src python scripts/build_prompt_batch.py \
  --target-json examples/example_campaign/target.json \
  --hypothesis-json examples/example_campaign/hypothesis.json \
  --candidate-dir data/results/manual_round/records \
  --campaign-id CAMP-001 \
  --run-id RUN-PROMPT-001 \
  --output-dir data/phase2/prompt_batch
```

Expected artifacts:
- `prompt_batch_manifest.json`
- `prompt_batch.jsonl`
- `packets/*.json`

### review_results

Purpose:
Attach result artifacts to candidates, classify failure modes, update statuses, and generate closed-loop recommendations.

Primary command:

```bash
PYTHONPATH=src python scripts/run_result_review.py \
  --candidate-records-dir data/results/manual_round/records \
  --result examples/example_campaign/results/simulated_result_AMP_SRC_DBAASP_1001.md \
  --campaign-id CAMP-001 \
  --run-id RUN-REVIEW-001 \
  --output-dir data/results/manual_round \
  --base-dag-json data/results/manual_round/research_graph.json
```

Expected artifacts:
- `closed_loop_recommendations.json`
- `campaign_recommendation_plan.json`
- `next_round_plan.json`
- `campaign_decision.json`
- `research_graph_result_review.json`
- `result_review_report.md`

### run_active_learning

Purpose:
Rank candidate records and select a next batch using the active-learning simulator.

Primary command:

```bash
PYTHONPATH=src python scripts/run_active_learning_simulator.py \
  --candidate-records-dir data/results/manual_round/records \
  --campaign-id CAMP-001 \
  --run-id RUN-AL-001 \
  --batch-size 5 \
  --output-dir data/phase2/active_learning \
  --base-dag-json data/results/manual_round/research_graph.json
```

Expected artifacts:
- `active_learning_plan.json`
- `active_learning_rankings.json`
- `active_learning_scoring_summary_prompt.json`
- `active_learning_report.md`
- `research_graph_active_learning.json`

### summarize_campaign

Purpose:
Explain the current campaign state in plain language with links to artifacts and a short next-step recommendation.

Future supporting script:

```text
scripts/summarize_campaign_state.py
```

Expected summary fields:
- Campaign id
- Latest target and hypothesis
- Candidate count by status
- Latest manual round
- Latest prompt batch
- Latest result review
- Latest active-learning plan
- Missing or stale artifacts
- Recommended next command

### recommend_next_slice

Purpose:
Compare repo state to `docs/planning/roadmap.md` and recommend the next implementation slice.

Expected behavior:
- Do not assume roadmap checkboxes are complete unless corresponding files or tests exist
- Prefer the smallest useful vertical slice
- Explain why that slice comes next

## Artifact Contracts

The plugin should treat these as authoritative:
- `schemas/*.schema.json`
- `src/peptide_flywheel/models.py`
- `src/peptide_flywheel/validation.py`
- Generated JSON records under workflow output directories
- Research DAG JSON files

Before running a workflow, the plugin should check that required inputs exist and have the expected artifact type.

After running a workflow, the plugin should report:
- command run
- artifacts created
- validation warnings or errors
- whether tests were run
- next recommended action

## Safety Scope

The plugin is for computational research organization, artifact generation, validation, and planning.

It may:
- Summarize target/candidate/result artifacts
- Run repository scripts
- Produce structured planning recommendations
- Generate prompt packets for controlled review

It must not:
- Provide wet-lab synthesis protocols
- Provide dosing, clinical, therapeutic, or patient guidance
- Claim a candidate is safe or effective
- Present simulated outputs as experimental truth
- Hide uncertainty or validation failures

## Roadmap

### Plugin Phase A: Repo-scoped skill spec

- [x] Define plugin purpose and boundaries
- [x] Define repo marker checks
- [x] Define named workflows
- [x] Define safety scope

### Plugin Phase B: Operator docs

- [ ] Add `agent/workflow_recipes.md`
- [ ] Add `agent/artifact_contracts.md`
- [ ] Add `agent/campaign_state_checklist.md`
- [ ] Add `agent/safety_scope.md`

### Plugin Phase C: Stable state summarizer

- [ ] Add `scripts/summarize_campaign_state.py`
- [ ] Add JSON output mode
- [ ] Add markdown output mode
- [ ] Add tests for campaign state inference

### Plugin Phase D: Codex skill packaging

- [ ] Create `SKILL.md`
- [ ] Link reference docs
- [ ] Add repo-scope refusal behavior
- [ ] Add workflow command recipes
- [ ] Test skill behavior inside this repo

### Plugin Phase E: Optional fuller plugin

- [ ] Add helper tools only if the skill proves insufficient
- [ ] Keep scientific logic in the core repo
- [ ] Use plugin tools only for orchestration, state summaries, and guardrails
