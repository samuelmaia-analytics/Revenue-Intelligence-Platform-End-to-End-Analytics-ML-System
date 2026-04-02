[CmdletBinding()]
param(
    [string]$Python = "py -3.11",
    [switch]$SkipEnvCopy
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$envExample = Join-Path $projectRoot ".env.example"
$envFile = Join-Path $projectRoot ".env"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "==> $Message"
    & $Action
}

if (-not (Test-Path $venvPython)) {
    Invoke-Step -Message "Creating .venv with $Python" -Action {
        Invoke-Expression "$Python -m venv `"$venvPath`""
    }
}

Invoke-Step -Message "Upgrading pip" -Action {
    & $venvPython -m pip install --upgrade pip
}

Invoke-Step -Message "Installing project with dev dependencies" -Action {
    & $venvPython -m pip install -e "$projectRoot[dev]"
}

if (-not $SkipEnvCopy -and (Test-Path $envExample) -and -not (Test-Path $envFile)) {
    Invoke-Step -Message "Creating .env from .env.example" -Action {
        Copy-Item $envExample $envFile
    }
}

Write-Host ""
Write-Host "Bootstrap completed."
Write-Host "Use: .\.venv\Scripts\python.exe -m pytest -q"
