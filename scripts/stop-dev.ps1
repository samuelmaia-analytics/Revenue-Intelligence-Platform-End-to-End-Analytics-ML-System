[CmdletBinding()]
param(
    [ValidateSet("app", "api", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = (Join-Path $projectRoot ".venv\Scripts\python.exe").ToLowerInvariant()

function Get-ProjectPythonProcesses {
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            $_.ExecutablePath.ToLowerInvariant() -eq $venvPython
        }
}

function Matches-Target {
    param(
        [Parameter(Mandatory = $true)]
        $Process,
        [Parameter(Mandatory = $true)]
        [string]$SelectedTarget
    )

    $commandLine = [string]$Process.CommandLine
    if ($SelectedTarget -eq "all") {
        return $true
    }
    if ($SelectedTarget -eq "app") {
        return $commandLine -like "*streamlit*" -or $commandLine -like "*app/streamlit_app.py*"
    }
    if ($SelectedTarget -eq "api") {
        return $commandLine -like "*uvicorn*" -or $commandLine -like "*services.api.main:app*"
    }
    return $false
}

$processes = @(Get-ProjectPythonProcesses | Where-Object { Matches-Target -Process $_ -SelectedTarget $Target })

if ($processes.Count -eq 0) {
    Write-Host "No matching dev processes found."
    exit 0
}

foreach ($process in $processes) {
    Write-Host "==> Stopping pid=$($process.ProcessId)"
    Stop-Process -Id $process.ProcessId -Force
}

Write-Host ""
Write-Host "Stopped $($processes.Count) process(es)."
