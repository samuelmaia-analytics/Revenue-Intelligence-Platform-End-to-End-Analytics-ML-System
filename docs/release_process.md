# Release Process

## Purpose

This repository does not need heavyweight release management. It does need a clear rule for when a change is ready to be presented as a stable portfolio increment.

## Release Trigger

Create a release when at least one of these is true:

- a governed output contract changes
- a runtime policy changes
- a new operational capability is added
- the dashboard or API consumption path changes materially
- documentation changes the way reviewers should understand the system

## Release Checklist

Before tagging a release:

1. run the full validation suite
2. confirm the dashboard smoke check passes
3. confirm `README`, `runbook` and relevant ADRs still match implementation
4. confirm output contracts and processed artifact validation still reflect reality
5. confirm no generated local runtime noise is being committed by accident
6. if runtime shape changed intentionally, refresh `metrics/runtime_baseline.json` using the manual runtime-baseline workflow or `make update-runtime-baseline`

Validation commands:

```powershell
python -m pytest -q
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python scripts/smoke_dashboard.py
python scripts/smoke_api.py
python scripts/smoke_downstream_sql.py
python scripts/smoke_processed_exports.py
python scripts/smoke_partner_payload.py
python scripts/smoke_dbt_sqlite.py
python -m pytest -q tests/test_repository_governance.py tests/test_operational_assets.py
python -m build
```

If containers, SQL portability, or repository policy change materially, also review:

- `docs/governance_framework.md`
- `docs/ci_cd.md`
- `sql/README.md`
- `.github/workflows/ci.yml`

## Release Notes Standard

Each release note should answer:

- what changed
- why it matters
- what contracts or operational behavior changed
- what reviewers should look at first

Good release notes are short and technical. Avoid marketing language.

## Release Scope Rule

Do not mix unrelated changes just to make a release look larger.

Good release examples:

- pipeline reliability hardening
- dashboard modularization plus smoke coverage
- processed artifact validation plus contract updates

Bad release examples:

- random refactors, copy edits and formatting churn grouped together
- speculative features with no validation
- aspirational roadmap items documented as if released

## Recommended Flow

1. merge a coherent change set
2. update docs that changed behavior or evaluation narrative
3. add or update a file in `docs/releases/`
4. tag the version
5. use the release note as the public summary for GitHub reviewers
6. verify the changelog entry and release note describe the same operational delta

## Runtime Baseline Maintenance

When performance changes intentionally and the new runtime is acceptable:

1. run the manual workflow `.github/workflows/runtime-baseline.yml` to generate runtime evidence and open a PR automatically, with squash auto-merge attempted when repository policy allows it, or run `make update-runtime-baseline` after a fresh pipeline execution
2. review the diff in `metrics/runtime_baseline.json`
3. confirm the CI runtime regression gate still passes against the refreshed baseline
4. mention the baseline update in release notes if the change is material

## Current Release Artifact

Existing release notes live in:

- [docs/releases/v1.0.0.md](releases/v1.0.0.md)
- [docs/releases/v1.1.0.md](releases/v1.1.0.md)
- [docs/releases/v1.2.0.md](releases/v1.2.0.md)
- [docs/releases/v1.3.0.md](releases/v1.3.0.md)
- [docs/releases/v1.3.1.md](releases/v1.3.1.md)
- [docs/releases/v1.3.2.md](releases/v1.3.2.md)
- [docs/releases/v1.3.3.md](releases/v1.3.3.md)
