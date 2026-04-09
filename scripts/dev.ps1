[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "dev\start.ps1"
& $scriptPath @Args
exit $LASTEXITCODE
