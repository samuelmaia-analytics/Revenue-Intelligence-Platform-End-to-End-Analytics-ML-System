# Environment Model

This repository intentionally keeps the environment story small and explicit.

## Supported Environments

### Local application environment

Purpose:
- run the batch pipeline
- run tests
- run Streamlit
- run the API smoke

Interpreter:
- `.venv\Scripts\python.exe`

Packages:
- `requirements.txt`
- `requirements-dev.txt`

### Local dbt CLI environment

Purpose:
- run `dbt` without destabilizing the application environment

Interpreter:
- `.dbt-venv\Scripts\python.exe`

Packages:
- `dbt-core`
- `dbt-sqlite`

Rule:
- do not install `dbt` into `.venv`

### CI environment

Purpose:
- prove that lint, tests, smokes, build, dbt validation, and container paths still work

Owner:
- `.github/workflows/ci.yml`

### Hosted reference environment

Purpose:
- demonstrate a realistic promotion path beyond local-only execution
- run the same packaged application surface inside containers

Current reference shape:
- Streamlit container from `Dockerfile`
- API container from `Dockerfile.api`
- GitHub Actions as the canonical automated verification environment

Rule:
- hosted examples must keep `python -m src.pipeline run` as the canonical batch path
- hosted surfaces may consume packaged artifacts, but should not fork orchestration logic

### Optional Postgres validation environment

Purpose:
- validate that the warehouse persistence path can target Postgres without changing pipeline orchestration
- prove compatibility before adopting a non-SQLite warehouse in a richer environment

Activation:
- set `RIP_SMOKE_POSTGRES_URL`
- optionally set `RIP_SMOKE_POSTGRES_SCHEMA`
- run `python scripts/smoke_postgres_optional.py` or `make smoke-postgres-optional`

Rule:
- this is an optional smoke path, not the default developer requirement
- if the URL is absent or SQLAlchemy is not installed, the smoke exits as `skipped`

## Environment Rules

1. `.venv` is the default runtime for application code.
2. `.dbt-venv` exists only to isolate the `dbt` CLI.
3. CI is the canonical reference for what must stay green.
4. Local success is not enough if CI does not validate the same surface.
5. The package install path `pip install -e .[dev]` is the preferred developer bootstrap.
6. SQLite remains the default system-of-record warehouse for local work.
7. Postgres is the next validation target, not a second orchestration path.

## Typical Commands

Application runtime:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\smoke_dashboard.py
.venv\Scripts\python.exe scripts\smoke_api.py
```

dbt runtime:

```powershell
.venv\Scripts\python.exe scripts\smoke_dbt_sqlite.py
.dbt-venv\Scripts\dbt.exe --project-dir dbt run
```

## Drift Prevention

If a command succeeds only outside `.venv`, that is usually environment drift rather than a code fix.

If `dbt` requires a dependency change that breaks Streamlit or the API, fix the environment boundary first instead of weakening the application stack.

## Warehouse Target Evolution Plan

Current state:
- SQLite is the default for local reproducibility, CI determinism, and low setup cost.

Near-term target:
- optional Postgres smoke validation using `RIP_SMOKE_POSTGRES_URL`
- keep the same batch orchestration, contracts, and manifests

Later production-oriented target:
- externalized warehouse credentials by environment
- schema migration strategy per target
- stronger downstream assertions for Postgres-specific persistence behavior

Recommended smoke shape:
- use a non-default schema prefix such as `analytics_smoke`
- keep the same pipeline contract and runtime path
- treat the schema-prefixed smoke as compatibility evidence, not as a second warehouse implementation

The migration principle is simple: evolve the persistence target without creating parallel runtime logic.
