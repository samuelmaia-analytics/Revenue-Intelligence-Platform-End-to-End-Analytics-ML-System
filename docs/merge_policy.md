# Merge Policy

## Purpose

This repository does not need heavy process. It does need clear merge expectations so quality does not depend on memory or enthusiasm.

## Required Labels

Recommended labels for issues and pull requests:

- `runtime`
- `data-quality`
- `warehouse`
- `dashboard`
- `api`
- `dbt`
- `docs`
- `breaking-change`

These labels are intentionally small. They should describe the primary surface affected, not every possible side effect.

## Merge Gate

Do not merge unless all relevant checks are green:

- lint and static checks
- pytest suite
- repository governance tests
- dashboard smoke
- API smoke
- downstream SQL smoke
- processed exports smoke
- partner payload smoke
- dbt SQLite smoke
- package build

## Review Expectations

Every PR should make these points obvious:

1. what changed
2. why it changed
3. what runtime surface is affected
4. what validation was run
5. what residual risks remain
6. what documentation or governance surfaces were intentionally reviewed

## Merge Rule

Prefer squash merge for coherent, reviewable changes.

Do not merge:

- mixed-scope PRs with unrelated changes
- undocumented contract changes
- runtime behavior changes without matching tests or docs
- "cleanup" PRs that weaken the official execution path

## Release Alignment

If a PR changes runtime behavior, contracts, dashboard behavior, dbt assumptions, or reviewer-facing documentation, it should also consider:

- `CHANGELOG.md`
- `docs/releases/`
- `docs/runbook.md`
- `README.md`
- `docs/governance_framework.md`
- `docs/ci_cd.md`
