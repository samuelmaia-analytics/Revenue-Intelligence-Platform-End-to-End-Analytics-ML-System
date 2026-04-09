[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "demo\enterprise.ps1"
& $scriptPath @Args
exit $LASTEXITCODE
