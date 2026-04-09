[CmdletBinding()]
param(
    [switch]$RunPipelineFirst,
    [switch]$StartApi,
    [switch]$OpenBundle
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

if ($RunPipelineFirst) {
    & (Join-Path $PSScriptRoot "dev\start.ps1") -Target pipeline
}

if ($StartApi) {
    & (Join-Path $PSScriptRoot "dev\start.ps1") -Target api -SkipPipeline
}

& (Join-Path $PSScriptRoot "dev\start.ps1") -Target app -SkipPipeline

if ($OpenBundle) {
    & (Join-Path $PSScriptRoot "demo\generate_bundle.ps1")
}

Write-Host ""
Write-Host "Canonical local demo is running."
Write-Host "Streamlit: http://127.0.0.1:8501"
if ($StartApi) {
    Write-Host "API: http://127.0.0.1:8000"
}
