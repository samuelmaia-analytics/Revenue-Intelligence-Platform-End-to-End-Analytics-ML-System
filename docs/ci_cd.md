# CI/CD Surface

## Purpose

CI exists to prove that the repository is reproducible, reviewable, and operationally coherent. It is not only a unit-test runner.

## Workflow Topology

The main workflow in `.github/workflows/ci.yml` is split into focused jobs:

- `quality`: formatting, linting, typing, tests, smoke scripts, and package build
- `governance`: repository-governance and operational-asset tests
- `dbt-sqlite`: pipeline execution followed by dbt-on-SQLite validation
- `docker`: container image build plus API and batch container smoke validation

This split matters because it makes failures attributable:

- if `quality` fails, the code or core artifacts are inconsistent
- if `governance` fails, repository policy or documentation drifted
- if `dbt-sqlite` fails, downstream warehouse consumption regressed
- if `docker` fails, the deployable surface regressed

## Local To CI Parity

Local validation should mirror CI as closely as practical:

```powershell
make verify
make governance
make docker-build
```

Use direct commands when isolating a failure, but keep the official commands documented and shared.

## Required Gates

The workflow is expected to keep these signals green before merge:

- `python -m ruff check .`
- `python -m black --check .`
- `python -m isort --check-only .`
- `python -m mypy src services contracts main.py`
- `python -m pytest -q`
- dashboard, API, SQL, processed-export, partner-payload, and dbt smoke checks
- package build
- repository-governance and operational-asset tests
- container smoke validation

## Artifact Expectations

CI should produce evidence, not only pass/fail signals:

- processed manifest
- quality report
- KPI snapshot
- curated recommendation exports

If a change removes or renames one of these artifacts, update the runbook, smoke checks, and release notes in the same change set.

## Change Discipline

Update CI when:

- a new governed downstream surface is introduced
- local verification changes materially
- the official runtime path or required artifact set changes
- a review failure would be easier to diagnose with isolated job boundaries

Do not expand CI with fashionable checks that do not improve repository trust.
