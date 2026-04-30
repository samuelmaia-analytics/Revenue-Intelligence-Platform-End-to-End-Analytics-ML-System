# Contributing

## Purpose

Treat this repository as a compact, production-minded data system.

That means contributions should improve one or more of the following:

- correctness
- reliability
- maintainability
- observability
- reproducibility
- reviewer trust

Changes that only make the repository look busier are out of scope.

## First Read

Before changing code, read:

- [README.md](README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
- [docs/repository_structure.md](docs/repository_structure.md)
- [docs/merge_policy.md](docs/merge_policy.md)
- [docs/deprecation_policy.md](docs/deprecation_policy.md)

## Engineering Principles

- `python -m src.pipeline run` is the official execution path.
- Optional surfaces must consume the batch core, not replace it.
- Prefer explicit contracts, manifests, and validation over implicit behavior.
- Keep abstractions proportional to the size of the repository.
- Document implemented behavior only. Do not write aspirational docs.
- If a change increases complexity, its operational payoff must be obvious.

## High-Signal Contributions

Strong changes usually improve:

- runtime reliability
- type safety and boundary clarity
- artifact validation
- warehouse correctness
- debuggability and failure evidence
- onboarding quality
- regression protection

Low-signal changes to avoid:

- speculative abstractions
- framework churn without a clear benefit
- broad renames without a structural payoff
- documentation that promises behavior the code does not implement
- “portfolio polish” that does not improve engineering quality

## Repository Boundaries

Preferred placement:

- `src/`: batch runtime, data services, modeling, reporting, pipeline logic
- `contracts/`: governed schemas and compatibility paths
- `services/`: service interfaces such as the API
- `app/`: Streamlit presentation layer
- `scripts/`: smoke checks and lightweight operational helpers
- `tests/`: regression coverage
- `docs/`: architecture, onboarding, runbooks, ADRs, release notes
- `dbt/`: downstream analytical layer on trusted warehouse outputs

Canonical imports should be preferred over compatibility shims:

- `contracts.v1.data_contract`
- `services.api.main`

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
Copy-Item .env.example .env
pre-commit install
```

Optional dbt environment:

```powershell
python -m venv .dbt-venv
.\.dbt-venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install dbt-core dbt-sqlite
```

## Standard Workflow

1. Create a focused branch.
2. Make one coherent change set.
3. Update tests and docs where behavior changes.
4. Run the relevant validation commands.
5. Open a PR using the repository template.

Prefer smaller PRs with one operational theme over mixed changes.

## Validation Expectations

Minimum expected before opening a PR:

```powershell
make verify-core
```

For changes that touch downstream surfaces, also run:

```powershell
make verify
```

Equivalent direct commands:

```powershell
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python -m mypy src services contracts main.py
python -m pytest -q
python scripts/smoke_dashboard.py
python scripts/smoke_api.py
python scripts/smoke_downstream_sql.py
python scripts/smoke_processed_exports.py
python scripts/smoke_partner_payload.py
python scripts/smoke_dbt_sqlite.py
python -m build
```

If the container path is affected, also validate:

```powershell
make docker-build
make docker-smoke
```

## Testing Standard

Add or update tests when changing:

- pipeline orchestration
- config resolution
- backfill, retry, retention, freshness, or quality policy
- manifests, snapshots, or runtime evidence
- warehouse persistence or downstream consumption
- governed contracts
- CLI behavior
- API request or registry behavior
- dashboard data loading or smoke surfaces

If no test is added, explain why current coverage is sufficient.

## Documentation Standard

Documentation must track behavior, not intention.

Review at least the relevant subset of:

- [README.md](README.md)
- [README.pt-BR.md](README.pt-BR.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
- [docs/release_process.md](docs/release_process.md)

## Commit Convention

Use lightweight conventional commits:

- `feat:` new capability
- `fix:` defect correction
- `refactor:` internal improvement without intentional behavior change
- `test:` test-only change
- `docs:` documentation-only change
- `chore:` tooling, maintenance, or dependency work

Examples:

- `feat: add runtime artifact service layer`
- `fix: fail fast on invalid backfill window`
- `refactor: extract pipeline runtime manifest helpers`
- `test: cover external raw seed precedence`
- `docs: tighten reviewer-facing repository guide`

Do not use:

- `update stuff`
- `misc changes`
- `final version`

## Pull Request Standard

Use the template in [.github/pull_request_template.md](.github/pull_request_template.md).

A good PR should make it easy to answer:

- what changed
- why it changed
- what risk it addresses
- how it was validated
- what residual risk remains

## Review Bar

A change is not ready if:

- it increases complexity without reducing a real risk
- it weakens the batch pipeline as the system of record
- it changes artifacts without validation
- it changes behavior without updating docs
- it makes the repository harder to inspect or reason about

## Merge Discipline

Before merge:

- CI must pass
- unresolved review comments must be closed
- documentation and tests must match behavior
- commit titles should follow the commit convention

Merge policy details live in [docs/merge_policy.md](docs/merge_policy.md).
