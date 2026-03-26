# Contributing

## Working Standard

Treat this repository as a small, production-minded data system.

That means:

- optimize for clarity, reliability, and reproducibility
- keep the batch pipeline as the system of record
- prefer explicit contracts over implicit behavior
- document real behavior, not desired future behavior
- avoid adding complexity unless it clearly reduces operational risk

## Before You Change Code

Read these files first:

- [README.md](README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/governance_framework.md](docs/governance_framework.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
- [docs/repository_structure.md](docs/repository_structure.md)
- [docs/deprecation_policy.md](docs/deprecation_policy.md)
- [docs/merge_policy.md](docs/merge_policy.md)
- [docs/ci_cd.md](docs/ci_cd.md)
- [docs/incident_playbooks.md](docs/incident_playbooks.md)

## Contribution Principles

- one official execution path: `python -m src.pipeline run`
- optional interfaces must consume the batch core instead of becoming alternate orchestration centers
- every meaningful change should reduce risk, improve maintainability, or improve reviewer trust
- low-signal refactors should not displace higher-signal reliability or correctness work

## High-Signal Changes

Strong changes usually improve one or more of these:

- runtime reliability
- contract clarity
- artifact validation
- warehouse consumption correctness
- observability and debuggability
- documentation fidelity
- regression protection

Low-signal changes to avoid:

- speculative abstractions
- framework churn without operational payoff
- broad renames without structural improvement
- aspirational documentation for features that do not exist

## Local Workflow

Setup:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Common commands:

```powershell
make verify
make smoke-dashboard
make smoke-api
make smoke-dbt
make pipeline
```

Equivalent direct commands:

```powershell
python -m src.pipeline run
python scripts/smoke_dashboard.py
python -m pytest -q
```

## Validation Expectations

Run before opening a PR:

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
python -m pytest -q tests/test_repository_governance.py tests/test_operational_assets.py
python -m build
```

If your change affects the container path, also validate:

```powershell
docker build -t revenue-intelligence .
docker run --rm revenue-intelligence python -m src.pipeline run --log-level INFO
docker build -f Dockerfile.api -t revenue-intelligence-api .
```

## Repository Boundaries

Placement rules:

- `src/`: batch pipeline and domain logic
- `app/`: Streamlit consumption layer
- `services/`: runtime-facing APIs and interfaces
- `contracts/`: governed schemas and compatibility paths
- `tests/`: behavioral and regression coverage
- `docs/`: documentation for implemented repository behavior
- `scripts/`: smoke checks and lightweight automation

For downstream smoke checks, prefer the shared temporary-runtime helper in `scripts/smoke_support.py` instead of duplicating bootstrap logic.

Canonical paths should be preferred over shims:

- `contracts.v1.data_contract`
- `services.api`

## Testing Standard

Add or update tests when changing:

- orchestration behavior
- manifests or snapshots
- config resolution
- warehouse persistence or consumption
- governed schemas
- CLI behavior
- failure handling
- retry, backfill, retention, freshness, or quality policy
- dashboard data loading or smoke behavior

If no test is added, the PR should explain why current coverage is sufficient.

## Documentation Standard

Update docs when behavior changes.

At minimum, review:

- `README.md`
- `README.pt-BR.md`
- `docs/architecture.md`
- `docs/runbook.md`
- `docs/troubleshooting_matrix.md`
- `docs/release_process.md`
- `docs/governance_framework.md`
- `docs/ci_cd.md`

Do not document planned behavior as if it already exists.

## Pull Request Standard

Use the template in:

- [.github/pull_request_template.md](.github/pull_request_template.md)

PRs should stay focused. Split changes when they mix unrelated concerns without a shared operational reason.

Merge and labeling guidance lives in:

- [docs/merge_policy.md](docs/merge_policy.md)

## Commit Convention

Use lightweight conventional commits:

- `feat:` for capability changes
- `fix:` for defects
- `refactor:` for internal code improvement without intentional behavior change
- `test:` for test-only work
- `docs:` for documentation-only changes
- `chore:` for maintenance and tooling

Good examples:

- `feat: add processed artifact validation stage`
- `fix: fail pipeline on invalid backfill window`
- `refactor: extract dashboard view composition`
- `test: add warehouse consumption regression coverage`
- `docs: publish release and runbook updates`

Bad examples:

- `update stuff`
- `final changes`
- `improve project`

## Review Bar

A change is not ready if:

- it increases complexity without clear operational payoff
- it weakens the batch core as the center of gravity
- it changes outputs without validation or documentation
- it introduces undocumented runtime behavior
- it makes the repository easier to misunderstand
