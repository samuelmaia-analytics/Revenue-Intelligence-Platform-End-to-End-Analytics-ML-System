# GitHub Actions Workflows

## Purpose

Provide a clear map of workflow intent, triggers, and expected evidence.

## Active Workflows

### `ci.yml`

Trigger:

- `push` to `main`
- `pull_request`

Main jobs:

- `hygiene`
- `quality`
- `governance`
- `windows-powershell`
- `dbt-sqlite`
- `docker`

Expected evidence:

- quality/test pass signals
- smoke validation across dashboard, API, SQL, exports, dbt
- container smoke evidence
- runtime/observability artifacts uploaded from CI

### `runtime-baseline.yml`

Trigger:

- `workflow_dispatch`

Purpose:

- regenerate and validate `metrics/runtime_baseline.json`
- open PR with refreshed baseline and review labels

### `dbt-docs.yml`

Trigger:

- `workflow_dispatch`

Purpose:

- build and publish dbt documentation artifacts for downstream review

## Governance Rules for Workflows

- Keep one official batch execution center: `python -m src.pipeline run`.
- Add new workflow jobs only when they improve failure attribution or compliance confidence.
- Prefer reproducible artifact outputs over opaque pass/fail signals.
- When workflow behavior changes materially, update:
  - `docs/ci_cd.md`
  - `docs/governance_framework.md`
  - `README.md` (and localized READMEs when relevant)

## Operational Triage

- Failing `hygiene` or `governance`: repository-policy/docs drift likely.
- Failing `quality`: code, tests, or local parity regression.
- Failing `dbt-sqlite`: downstream warehouse contract regression.
- Failing `docker`: deployable runtime surface regression.
