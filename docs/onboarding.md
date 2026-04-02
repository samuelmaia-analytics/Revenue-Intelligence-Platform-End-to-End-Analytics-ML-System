# Onboarding Guide

## Objective

Get a new contributor from clone to a validated local run quickly, with minimal ambiguity.

Windows-first operational flow:

- `docs/windows_workflow.md`

## 1. Environment Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
copy .env.example .env
```

Windows shortcut:

```powershell
.\scripts\bootstrap.ps1
```

Recommended interpreter:

- `.venv\Scripts\python.exe`

Optional isolated dbt CLI:

```powershell
py -3.11 -m venv .dbt-venv
.\.dbt-venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install dbt-core dbt-sqlite
```

## 2. First Successful Run

Run the official batch path:

```powershell
python -m src.pipeline run
```

Expected outputs:

- `data/processed/pipeline_manifest.json`
- `data/processed/quality_report.json`
- `data/processed/executive_report.json`
- `data/warehouse/revenue_intelligence.db`

## 3. Validation Commands

```powershell
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python -m mypy src services contracts main.py
python -m pytest -q --cov=src --cov=services --cov=contracts --cov-report=term-missing
python scripts/smoke_dashboard.py
python scripts/smoke_api.py
python scripts/smoke_downstream_sql.py
python scripts/smoke_processed_exports.py
python scripts/smoke_partner_payload.py
python scripts/smoke_dbt_sqlite.py
python -m build
```

Windows shortcut:

```powershell
.\scripts\verify.ps1
.\scripts\verify.ps1 -IncludeSmokes
```

Clean package-install smoke:

```powershell
python -m venv .install-smoke-venv
.\.install-smoke-venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pip check
python -m src.pipeline --help
```

## 4. Optional Interfaces

Dashboard:

```powershell
python -m streamlit run app/streamlit_app.py
```

Windows shortcut:

```powershell
.\scripts\dev.ps1 -Target app
```

API:

```powershell
python -m uvicorn services.api.main:app --reload
```

Windows shortcut:

```powershell
.\scripts\dev.ps1 -Target api
.\scripts\dev.ps1 -Target all
.\scripts\status-dev.ps1
.\scripts\stop-dev.ps1 -Target all
```

dbt:

```powershell
.dbt-venv\Scripts\dbt.exe --project-dir dbt run
```

## 5. Repository Reading Order

Recommended reading sequence:

1. `README.md`
2. `docs/architecture.md`
3. `docs/repository_structure.md`
4. `src/pipeline.py`
5. `src/orchestration.py`
6. `docs/runtime_surfaces.md`
7. `docs/environments.md`

## 6. Common Failure Modes

- Missing dependencies in the active interpreter
  Use `.venv\Scripts\python.exe`
- dbt works in one shell but breaks the app environment
  Keep `dbt` isolated in `.dbt-venv`
- Empty or stale generated data
  Re-run `python -m src.pipeline run`
- Dashboard load errors
  Confirm processed artifacts exist under `data/processed/`

## 7. Contribution Standard

Before opening a PR:

- keep the batch CLI as the official path
- update docs if runtime behavior changed
- add or update tests for any behavior change
- avoid introducing alternate orchestration paths
