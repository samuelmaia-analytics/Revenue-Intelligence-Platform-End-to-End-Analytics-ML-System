[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "dev\status.ps1"
& $scriptPath
exit $LASTEXITCODE
