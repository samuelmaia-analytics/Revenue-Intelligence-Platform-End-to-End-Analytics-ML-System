$ErrorActionPreference = "Stop"

$listener = Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1

if (-not $listener) {
    Write-Output "No MySQL listener found on port 3306."
    exit 0
}

Stop-Process -Id $listener.OwningProcess -Force
Write-Output "Stopped MySQL process $($listener.OwningProcess)."
