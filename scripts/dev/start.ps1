[CmdletBinding()]
param(
    [ValidateSet("app", "api", "pipeline", "all")]
    [string]$Target = "app",
    [string]$BindHost = "127.0.0.1",
    [int]$ApiPort = 8000,
    [int]$AppPort = 8501,
    [switch]$SkipPipeline
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "Project virtual environment not found at .venv. Run .\scripts\bootstrap.ps1 first."
}

function Start-ManagedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "==> Starting $Name"
    $process = Start-Process -FilePath $venvPython -ArgumentList $Arguments -WorkingDirectory $projectRoot -PassThru
    Write-Host "    pid=$($process.Id)"
    return $process
}

function Invoke-ManagedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "==> Running $Name"
    & $venvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

function Start-App {
    Start-ManagedProcess -Name "streamlit" -Arguments @(
        "-m", "streamlit", "run", "app/streamlit_app.py",
        "--server.address", $BindHost,
        "--server.port", "$AppPort"
    ) | Out-Null
    Write-Host "    url=http://$BindHost`:$AppPort"
}

function Start-Api {
    Start-ManagedProcess -Name "api" -Arguments @(
        "-m", "uvicorn", "services.api.main:app",
        "--host", $BindHost,
        "--port", "$ApiPort",
        "--reload"
    ) | Out-Null
    Write-Host "    url=http://$BindHost`:$ApiPort"
}

function Run-Pipeline {
    Invoke-ManagedCommand -Name "pipeline" -Arguments @("-m", "src.pipeline", "run")
}

switch ($Target) {
    "pipeline" {
        Run-Pipeline
    }
    "app" {
        if (-not $SkipPipeline) {
            Run-Pipeline
        }
        Start-App
    }
    "api" {
        if (-not $SkipPipeline) {
            Run-Pipeline
        }
        Start-Api
    }
    "all" {
        if (-not $SkipPipeline) {
            Run-Pipeline
        }
        Start-Api
        Start-App
    }
}

Write-Host ""
Write-Host "Dev command completed."
Write-Host "Use Get-Process python | Where-Object { `$_.Path -like '*\\.venv\\Scripts\\python.exe' } to inspect running services."
