param(
    [switch]$Build,
    [switch]$RunPipelineFirst
)

$ErrorActionPreference = "Stop"

if ($RunPipelineFirst) {
    .\.venv\Scripts\python.exe -m src.pipeline run
    .\.venv\Scripts\python.exe -m src.pipeline observability --output-path data/processed/observability_summary.json
}

$composeArgs = @("compose", "up")
if ($Build) {
    $composeArgs += "--build"
}

docker @composeArgs
