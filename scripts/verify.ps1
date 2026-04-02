[CmdletBinding()]
param(
    [switch]$IncludeSmokes
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$qualityTargets = @("src", "services", "api", "main.py")

if (-not (Test-Path $venvPython)) {
    throw "Project virtual environment not found at .venv. Run .\scripts\bootstrap.ps1 first."
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "==> $Message"
    & $venvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Message failed with exit code $LASTEXITCODE."
    }
}

Invoke-Step -Message "ruff" -Arguments (@("-m", "ruff", "check") + $qualityTargets)
Invoke-Step -Message "black" -Arguments (@("-m", "black", "--check") + $qualityTargets)
Invoke-Step -Message "isort" -Arguments (@("-m", "isort", "--check-only") + $qualityTargets)
Invoke-Step -Message "mypy" -Arguments @("-m", "mypy", "src", "services", "contracts", "main.py")
Invoke-Step -Message "pytest" -Arguments @("-m", "pytest", "-q")

if ($IncludeSmokes) {
    Invoke-Step -Message "smoke dashboard" -Arguments @("scripts/smoke_dashboard.py")
    Invoke-Step -Message "smoke api" -Arguments @("scripts/smoke_api.py")
    Invoke-Step -Message "smoke downstream sql" -Arguments @("scripts/smoke_downstream_sql.py")
    Invoke-Step -Message "smoke processed exports" -Arguments @("scripts/smoke_processed_exports.py")
    Invoke-Step -Message "smoke partner payload" -Arguments @("scripts/smoke_partner_payload.py")
    Invoke-Step -Message "smoke dbt sqlite" -Arguments @("scripts/smoke_dbt_sqlite.py")
}

Write-Host ""
Write-Host "Verification completed."
