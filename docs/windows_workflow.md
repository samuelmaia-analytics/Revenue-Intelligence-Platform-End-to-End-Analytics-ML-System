# Windows Workflow

## Objective

Provide one clear PowerShell-first path for bootstrapping, validating, running, inspecting, and stopping the project on Windows without depending on `make`.

## Prerequisites

- Windows PowerShell
- Python 3.11 available through `py -3.11` or installed directly

## 1. Bootstrap

Create or refresh the local virtual environment and install the project with development dependencies:

```powershell
.\scripts\bootstrap.ps1
```

What it does:

- creates `.venv` if missing
- upgrades `pip`
- installs `-e .[dev]`
- copies `.env.example` to `.env` when needed

## 2. Verify

Run the local high-signal validation path against the project virtual environment:

```powershell
.\scripts\verify.ps1
```

Full validation including smoke checks:

```powershell
.\scripts\verify.ps1 -IncludeSmokes
```

## 3. Run Dev Surfaces

Run pipeline only:

```powershell
.\scripts\dev.ps1 -Target pipeline
```

Run dashboard:

```powershell
.\scripts\dev.ps1 -Target app
```

Run API:

```powershell
.\scripts\dev.ps1 -Target api
```

Run API and dashboard together:

```powershell
.\scripts\dev.ps1 -Target all
```

Skip pipeline regeneration when outputs already exist:

```powershell
.\scripts\dev.ps1 -Target app -SkipPipeline
.\scripts\dev.ps1 -Target api -SkipPipeline
```

## 4. Inspect Running Services

List running project processes from the local `.venv`:

```powershell
.\scripts\status-dev.ps1
```

## 5. Stop Running Services

Stop everything started from the local `.venv`:

```powershell
.\scripts\stop-dev.ps1 -Target all
```

Stop only dashboard or API:

```powershell
.\scripts\stop-dev.ps1 -Target app
.\scripts\stop-dev.ps1 -Target api
```

## 6. Recommended Daily Flow

```powershell
.\scripts\bootstrap.ps1
.\scripts\verify.ps1
.\scripts\dev.ps1 -Target all
.\scripts\status-dev.ps1
.\scripts\stop-dev.ps1 -Target all
```

## 7. Common Failure Modes

- `make` not found
  Use the PowerShell scripts in `scripts/` instead of `make`.

- Tests fail with missing packages like `sklearn`
  You are probably using the global Python interpreter instead of `.venv`.

- API or dashboard starts with stale data
  Run `.\scripts\dev.ps1 -Target pipeline` or omit `-SkipPipeline`.

- Nothing appears in `status-dev.ps1`
  No project-bound Python processes are running from `.venv`.
