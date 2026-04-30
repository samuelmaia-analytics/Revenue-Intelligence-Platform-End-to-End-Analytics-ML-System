# Incident Playbooks

This document complements the runbook. Use it when the failure class is already known and you need the shortest credible containment path.

## Playbook: Processed Artifact Drift

Trigger:
- `artifact_validation_report.json` fails
- processed export smoke fails

Immediate actions:
1. identify the first missing or invalid artifact
2. compare it against `src/artifact_validation.py`
3. inspect the reporting stage that produced it
4. add or update a regression test before changing the contract

Do not:
- silently relax the contract
- reclassify a breaking change as a documentation fix

Example:
- `top_10_actions.csv` no longer matches `business_outcomes.json`

## Playbook: Warehouse and dbt Divergence

Trigger:
- downstream SQL smoke fails
- `dbt` smoke fails after a successful pipeline run

Immediate actions:
1. confirm `warehouse.<target>` succeeded in `pipeline_manifest.json`
2. inspect `data/warehouse/revenue_intelligence.db`
3. inspect `dbt/target/run_results.json`
4. identify whether the issue is warehouse persistence or dbt model logic

Do not:
- patch dbt models to fit stale warehouse state
- skip the smoke to get CI green

Example:
- `dbt` smoke starts failing after a warehouse column rename

## Playbook: Downstream Consumer Fails After a Successful Batch Run

Trigger:
- the pipeline finishes successfully
- a downstream smoke, dashboard, partner export, or warehouse consumer fails afterwards

Immediate actions:
1. inspect `pipeline_manifest.json` and confirm the run completed with the expected outputs
2. inspect `artifact_validation_report.json` and `quality_report.json`
3. identify whether the failure comes from a contract break, consumer assumption, or stale environment
4. contain by reverting the consumer or reverting the breaking artifact change, not by mutating outputs manually

Recovery path:
1. compare current processed artifacts with the last known good snapshot in `data/snapshots/`
2. rerun only after the breaking contract or consumer logic is understood
3. add a regression test at the producer or consumer boundary before merging the fix

Do not:
- patch generated artifacts by hand
- let a consumer redefine the source of truth
- weaken validation to make the smoke pass

Example:
- `recommendations.csv` stays valid, but the partner payload smoke fails because a consumer assumed an old column name

## Playbook: API Container Unhealthy

Trigger:
- API container smoke does not reach `/health`
- local API smoke passes but Docker path fails

Immediate actions:
1. inspect Docker logs
2. verify `RIP_MODEL_DIR` resolution inside the container
3. confirm models are present in the expected processed registry layout
4. rerun `scripts/smoke_api.py` locally before changing the image

Do not:
- weaken the health endpoint contract
- bypass model loading to make the container look healthy

Example:
- container boots but `/health` never stabilizes because the model registry path moved

## Playbook: Model Registry or Model Artifact Failure

Trigger:
- API smoke fails with model loading errors
- monitoring or executive reporting fails after model artifacts were regenerated
- registry metadata points to a missing or incompatible model version

Immediate actions:
1. inspect `data/processed/registry/` and confirm `latest.json` points to an existing version
2. inspect `pipeline_manifest.json` and `metrics_report.json` from the same run
3. verify that the expected model files exist and were produced by the current contract-compatible run
4. contain by restoring the last known good registry pointer or rerunning the producer, not by editing model metadata manually

Recovery path:
1. compare the current registry layout against the last good snapshot under `data/snapshots/`
2. rerun `scripts/smoke_api.py` after restoring the producer-consumer contract
3. add or update a regression test covering the missing model or registry mismatch

Do not:
- patch `latest.json` without understanding why the registry drifted
- bypass model loading in the API just to get health green
- commit a new model artifact without matching metrics and manifest evidence

Example:
- `latest.json` points to `model_v5`, but only `model_v4` exists after a partial local run

## Playbook: Dashboard Looks Correct but Business Slice Is Wrong

Trigger:
- Streamlit app loads
- users report wrong ranking or empty high-value segments

Immediate actions:
1. inspect `recommendations.csv`
2. inspect `top_10_actions.csv`
3. run `scripts/smoke_dashboard.py`
4. compare the selected filters with the processed export volume

Do not:
- move core ranking logic into the dashboard
- add UI-only corrections that diverge from processed outputs

Example:
- the dashboard ranking differs from `top_10_actions.csv` after a UI-only filter change

## Playbook: Environment Drift

Trigger:
- local validation diverges from CI
- dashboard or API smokes fail after dependency changes

Immediate actions:
1. confirm `.venv` is used for app and test runtime
2. confirm `.dbt-venv` is used only for `dbt` CLI
3. run `pip check` in `.venv`
4. rerun the relevant smoke instead of trusting installation success

Do not:
- install `dbt` into `.venv`
- use local caches as evidence that the environment is healthy

Example:
- local `dbt` starts working, but Streamlit breaks because `protobuf` was upgraded in `.venv`
