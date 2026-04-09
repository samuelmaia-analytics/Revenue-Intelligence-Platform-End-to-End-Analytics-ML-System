param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ApiKey = "rip-demo-token-v1"
)

$ErrorActionPreference = "Stop"
$headers = @{
    "X-API-Key" = $ApiKey
    "X-Request-ID" = "demo-export-run"
}

Write-Host "Health"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "`nExecutive Summary"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/executive-summary" -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "`nScorecard"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/scorecard" -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "`nInsight Draft"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/insight-draft" -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "`nReliability Report"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/reliability-report" -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "`nTop Actions CSV"
(Invoke-WebRequest -Uri "$BaseUrl/api/v1/exports/top-actions.csv" -Headers $headers).Content
