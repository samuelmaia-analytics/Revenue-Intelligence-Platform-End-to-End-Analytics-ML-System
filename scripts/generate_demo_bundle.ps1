[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "demo\generate_bundle.ps1"
& $scriptPath @Args
exit $LASTEXITCODE
