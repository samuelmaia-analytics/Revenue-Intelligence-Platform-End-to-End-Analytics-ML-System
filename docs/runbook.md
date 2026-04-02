# Operational Runbook

## Purpose

This runbook exists for one reason: make the repository operable by someone other than the original author.

It covers:

- how to run the official pipeline
- how to reprocess a time window
- how to inspect failures
- how to validate outputs before trusting them

## Official Commands

Standard batch run:

```powershell
python -m src.pipeline run
```

Reprocess a bounded historical window:

```powershell
python -m src.pipeline run --start-date 2025-01-01 --end-date 2025-03-31
```

Generate governance artifacts only:

```powershell
python -m src.pipeline artifacts
```

Dashboard smoke validation:

```powershell
python scripts/smoke_dashboard.py
```

API smoke validation:

```powershell
python scripts/smoke_api.py
```

dbt downstream smoke validation:

```powershell
python scripts/smoke_dbt_sqlite.py
```

Partner payload smoke validation:

```powershell
python scripts/smoke_partner_payload.py
```

## Pre-Run Checks

Before running:

1. confirm `.env` exists and matches the intended environment
2. confirm dependencies are installed in `.venv`
3. confirm `metrics/semantic_metrics.json` exists
4. confirm the raw input strategy:
   - source CSV in `data/raw/`, or
   - synthetic fallback if no source file is present

## Runtime Evidence

Every successful run should leave evidence in these locations:

- `data/processed/pipeline_manifest.json`
- `data/processed/quality_report.json`
- `data/processed/artifact_validation_report.json`
- `data/processed/freshness_report.json`
- `data/processed/runtime_metrics.json`
- `data/processed/run_events.jsonl`
- `data/manifests/`
- `data/runs/`
- `data/snapshots/`

Use these artifacts as the first debugging surface before changing code.

## Failure Investigation

When a run fails:

1. open the latest failure manifest in `data/manifests/*.failure.json`
2. inspect the `error_type`, `error_message`, `run_id` and stage timings
3. inspect `run_events.jsonl` to identify the last successful stage transition
4. open the run log referenced in the manifest
5. identify whether the failure belongs to:
   - input shape
   - quality gate
   - processed artifact validation
   - model training
   - warehouse persistence
   - API/runtime consumption
   - dbt downstream validation

## Common Failure Modes

### Missing required columns

Signal:
- failure in `validation.silver` or `validation.processed_artifacts`

Typical cause:
- upstream schema drift or changed export format

Action:
- inspect the raw file or processed artifact
- compare against `contracts/` and `src/artifact_validation.py`
- update code only if the contract change is intentional

### Quality gate failure

Signal:
- failure message mentions duplicates, referential issues or null fraction

Typical cause:
- degraded input quality or an unintended transformation regression

Action:
- inspect `quality_report.json`
- confirm whether data degradation is expected
- prefer fixing the transformation or input assumptions over relaxing the threshold

### Dashboard loads but looks empty

Signal:
- Streamlit runs but shows empty-state behavior

Typical cause:
- filtered slice has no matching recommendations
- processed outputs are stale or missing

Action:
- run `python scripts/smoke_dashboard.py`
- inspect `recommendations.csv`
- inspect selected filters in the sidebar

### Warehouse looks out of sync

Signal:
- processed artifacts exist but downstream SQL checks fail

Typical cause:
- persistence step failed or warehouse was inspected before the latest run completed

Action:
- inspect `pipeline_manifest.json`
- confirm the `warehouse.<target>` stage completed
- re-run the pipeline and inspect `data/warehouse/revenue_intelligence.db`

### API smoke fails

Signal:
- `python scripts/smoke_api.py` fails locally or the container smoke cannot reach `/health`

Typical cause:
- model registry not available in the expected path
- API auth configuration diverged from the smoke assumptions
- container booted but never exposed a healthy process

Action:
- inspect `services/api/main.py` health behavior
- confirm `RIP_MODEL_DIR`, `RIP_API_AUTH_MODE`, and `RIP_API_DEMO_TOKEN`
- confirm `/metrics` exposes counters and `X-Request-ID` is present on responses
- run the API smoke locally before changing the Docker path

### dbt smoke fails

Signal:
- `python scripts/smoke_dbt_sqlite.py` fails in CI or locally

Typical cause:
- warehouse was not rebuilt before dbt execution
- `dbt` CLI is missing from `.dbt-venv` or not discoverable
- dbt models no longer match the canonical warehouse outputs

Action:
- run `python -m src.pipeline run --log-level INFO`
- confirm `.dbt-venv\Scripts\dbt.exe --version`
- inspect `dbt/models/` and generated `dbt/target/run_results.json`
- update dbt contracts only if the runtime contract changed intentionally

### Environment bootstrap fails

Signal:
- dependency install succeeds for the app but `dbt` smoke or Streamlit runtime breaks afterward

Typical cause:
- CLI-only tooling was installed into `.venv` instead of `.dbt-venv`
- local cache or generated artifacts are masking a stale environment

Action:
- keep application dependencies in `.venv`
- keep CLI dbt dependencies in `.dbt-venv`
- run the relevant smoke tests after environment changes instead of trusting install success

## Output Validation Checklist

Before trusting a run:

1. `pipeline_manifest.json` status is success
2. `quality_report.json` exists and has no blocking issues
3. `artifact_validation_report.json` status is `ok`
4. `alerts_report.json` is reviewed if `status` is `warning`
5. `scripts/smoke_dashboard.py` passes if the UI is part of the release path
6. `scripts/smoke_api.py` passes if the API surface is part of the release path
7. `scripts/smoke_dbt_sqlite.py` passes if dbt artifacts or warehouse models changed
8. `scripts/smoke_processed_exports.py` passes if downstream CSV/JSON exports changed
9. `scripts/smoke_partner_payload.py` passes if partner-facing payload logic changed

## Safe Change Policy

When modifying the system:

- do not create alternate orchestration paths
- do not bypass artifact validation
- do not relax thresholds without documenting the reason
- do not change output contracts silently

If behavior changes intentionally, update:

- `README`
- `docs/architecture.md`
- `docs/runbook.md`
- relevant tests
