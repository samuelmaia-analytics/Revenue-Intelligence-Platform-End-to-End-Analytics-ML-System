# CI/CD Surface

## Purpose

CI exists to prove that the repository is reproducible, reviewable, and operationally coherent. It is not only a unit-test runner.

## Workflow Topology

The main workflow in `.github/workflows/ci.yml` is split into focused jobs:

- `hygiene`: fast repository policy and tracked-artifact checks
- `quality`: formatting, linting, typing, tests, smoke scripts, and package build
- `governance`: repository-governance and operational-asset tests
- `dbt-sqlite`: pipeline execution followed by dbt-on-SQLite validation
- `docker`: container image build plus dashboard, batch, and API container smoke validation

This split matters because it makes failures attributable:

- if `quality` fails, the code or core artifacts are inconsistent
- if `hygiene` fails, repository discipline regressed before heavier validation even starts
- if `governance` fails, repository policy or documentation drifted
- if `dbt-sqlite` fails, downstream warehouse consumption regressed
- if `docker` fails, at least one deployable surface regressed

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
- dashboard, batch, and API container smoke validation

## Artifact Expectations

CI should produce evidence, not only pass/fail signals:

- processed manifest
- quality report
- KPI snapshot
- runtime metrics artifact with runtime regression gate coverage
- observability summary derived from manifest, metrics, and event timeline artifacts
- versioned runtime baseline in `metrics/runtime_baseline.json`
- curated recommendation exports

If a change removes or renames one of these artifacts, update the runbook, smoke checks, and release notes in the same change set.

The docker job proves three independent runtime surfaces:

- `Dockerfile`: Streamlit dashboard container
- `Dockerfile.batch`: canonical batch runtime container
- `Dockerfile.api`: serving API container

## Runtime Baseline Workflow

The repository also keeps a manual workflow in `.github/workflows/runtime-baseline.yml` for controlled baseline refreshes.

Use it only when runtime behavior changed intentionally and the new performance envelope is acceptable.
The workflow refreshes the baseline, validates the gate, uploads the evidence, opens a labeled PR already routed for review, and attempts squash auto-merge when repository policy allows it.

## Change Discipline

Update CI when:

- a new governed downstream surface is introduced
- local verification changes materially
- the official runtime path or required artifact set changes
- a review failure would be easier to diagnose with isolated job boundaries

Do not expand CI with fashionable checks that do not improve repository trust.
