param(
    [switch]$Build,
    [switch]$RunPipelineFirst
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if ($RunPipelineFirst) {
    & $venvPython -m src.pipeline run
    & $venvPython -m src.pipeline observability --output-path (Join-Path $projectRoot "data\processed\observability_summary.json")
}

$composeArgs = @("compose", "up")
if ($Build) {
    $composeArgs += "--build"
}

Push-Location $projectRoot
try {
    docker @composeArgs
} finally {
    Pop-Location
}
