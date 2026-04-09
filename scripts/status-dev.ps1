[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = (Join-Path $projectRoot ".venv\Scripts\python.exe").ToLowerInvariant()

function Resolve-ProcessRole {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandLine
    )

    if (
        $CommandLine -like "*streamlit*" -or
        $CommandLine -like "*streamlit_app.py*" -or
        $CommandLine -like "*app/streamlit_app.py*"
    ) {
        return "app"
    }
    if ($CommandLine -like "*uvicorn*" -or $CommandLine -like "*services.api.main:app*") {
        return "api"
    }
    if ($CommandLine -like "*-m src.pipeline*" -or $CommandLine -like "*src\\pipeline.py*") {
        return "pipeline"
    }
    return "python"
}

$processes = @(
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            $_.ExecutablePath.ToLowerInvariant() -eq $venvPython
        } |
        ForEach-Object {
            $commandLine = [string]$_.CommandLine
            [PSCustomObject]@{
                Role = Resolve-ProcessRole -CommandLine $commandLine
                ProcessId = $_.ProcessId
                ExecutablePath = $_.ExecutablePath
                CommandLine = $commandLine
            }
        } |
        Sort-Object Role, ProcessId
)

if ($processes.Count -eq 0) {
    Write-Host "No dev processes are running for this project."
    exit 0
}

$processes | Format-Table -AutoSize Role, ProcessId, CommandLine
