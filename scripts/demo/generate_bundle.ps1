param(
    [string]$OutputDir = "demo_bundle",
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ApiKey = "rip-demo-token-v1"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$bundle = Join-Path $projectRoot $OutputDir
New-Item -ItemType Directory -Force -Path $bundle | Out-Null

Copy-Item (Join-Path $projectRoot "README.md") $bundle -Force
Copy-Item (Join-Path $projectRoot "docs\executive\one_pager.md") $bundle -Force
Copy-Item (Join-Path $projectRoot "docs\executive\technical_one_pager.md") $bundle -Force
Copy-Item (Join-Path $projectRoot "docs\commercial\proposal_template.md") $bundle -Force
Copy-Item (Join-Path $projectRoot "docs\commercial\commercial_deck.md") $bundle -Force
Copy-Item (Join-Path $projectRoot "docs\reliability_report.md") $bundle -Force
Copy-Item (Join-Path $projectRoot "docs\demo_walkthrough.md") $bundle -Force

if (Test-Path (Join-Path $projectRoot "data\processed\insight_draft.json")) { Copy-Item (Join-Path $projectRoot "data\processed\insight_draft.json") $bundle -Force }
if (Test-Path (Join-Path $projectRoot "data\processed\reliability_report.json")) { Copy-Item (Join-Path $projectRoot "data\processed\reliability_report.json") $bundle -Force }
if (Test-Path (Join-Path $projectRoot "data\processed\executive_summary.json")) { Copy-Item (Join-Path $projectRoot "data\processed\executive_summary.json") $bundle -Force }

try {
    $headers = @{ "X-API-Key" = $ApiKey; "X-Request-ID" = "demo-bundle" }
    Invoke-RestMethod -Uri "$BaseUrl/api/v1/scorecard" -Headers $headers | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $bundle "api_scorecard.json")
    Invoke-RestMethod -Uri "$BaseUrl/api/v1/reliability-report" -Headers $headers | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $bundle "api_reliability_report.json")
} catch {
    Write-Host "API exports skipped: $($_.Exception.Message)"
}

Write-Host "Demo bundle generated at $bundle"
