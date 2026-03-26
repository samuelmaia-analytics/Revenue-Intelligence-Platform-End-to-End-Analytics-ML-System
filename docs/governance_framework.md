# Governance Framework

## Purpose

This repository is intentionally small, but it still needs explicit governance so reviewers can trust that behavior, documentation, and operational evidence stay aligned.

## System of Record

The canonical runtime path is:

```powershell
python -m src.pipeline run
```

Everything else is downstream of that path:

- Streamlit reads governed artifacts
- the API serves governed outputs and model behavior
- the SQLite warehouse persists batch outputs
- dbt models consume warehouse state rather than replacing the batch core
- SQL examples describe approved analytical consumption patterns

## Governance Rules

1. Do not introduce a second orchestration center.
2. Do not change governed outputs without updating tests, contracts, and reviewer-facing docs.
3. Keep local-first reproducibility as the default unless an external dependency materially improves verification.
4. Prefer portable SQL for documented examples because the repository standard is SQLite-first.
5. Every operational claim in a README, runbook, or release note should map to code, tests, or automation already in the repo.

## Change Classes

Use these classes to reason about review depth and required evidence:

- `runtime`: changes pipeline execution, manifests, retries, backfill, freshness, or operational reports
- `contract`: changes governed schemas, exports, payloads, or compatibility shims
- `warehouse`: changes persisted SQLite structures or downstream analytical expectations
- `experience`: changes Streamlit, API, or other consumer-facing presentation layers
- `governance`: changes CI, repository policy, merge discipline, issue intake, or release process
- `docs`: changes reviewer understanding without changing runtime behavior

## Required Evidence By Change Type

- `runtime`: pytest coverage, smoke or operational validation, runbook review
- `contract`: contract validation, compatibility review, release note update when externally visible
- `warehouse`: SQL or dbt validation, portability check for SQLite-first examples
- `experience`: smoke validation and documentation if the interaction model changes
- `governance`: CI or repository-governance validation and updated policy docs
- `docs`: cross-check against implemented behavior and linked references

## Ownership Surfaces

- `src/` owns the official execution path and operational semantics
- `contracts/` owns governed schemas and compatibility windows
- `sql/` owns reference DDL and downstream analytical examples
- `dbt/` owns governed downstream transformation examples
- `.github/` owns merge, issue, and CI discipline
- `docs/` owns the reviewer narrative and operating model

## Release Alignment

When behavior changes materially, update the smallest coherent set that preserves reviewer trust:

- root README in the relevant languages
- runbook or troubleshooting docs when operation changes
- merge or release policy when governance changes
- release notes and changelog when portfolio narrative changes

## Review Standard

The repository should read as if a senior engineer expected another senior engineer to maintain it:

- narrow scope
- explicit trade-offs
- attributable failures
- consistent terminology
- no aspirational process presented as implemented capability
