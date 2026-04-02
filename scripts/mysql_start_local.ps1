$ErrorActionPreference = "Stop"

$mysqlBin = "C:\Program Files\MySQL\MySQL Server 8.4\bin"
$configRoot = "C:\ProgramData\MySQL\MySQL Server 8.4a"
$defaultsFile = Join-Path $configRoot "my.ini"
$dataDir = Join-Path $configRoot "data"
$logsDir = Join-Path $configRoot "logs"
$errorLog = Join-Path $logsDir "error.log"

if (-not (Test-Path $mysqlBin)) {
    throw "MySQL bin directory not found at $mysqlBin"
}

if (-not (Test-Path $defaultsFile)) {
    New-Item -ItemType Directory -Force -Path $dataDir, $logsDir | Out-Null
    @'
[mysqld]
basedir="C:/Program Files/MySQL/MySQL Server 8.4/"
datadir="C:/ProgramData/MySQL/MySQL Server 8.4a/data/"
port=3306
bind-address=127.0.0.1
character-set-server=utf8mb4
collation-server=utf8mb4_0900_ai_ci
log_error="C:/ProgramData/MySQL/MySQL Server 8.4a/logs/error.log"
'@ | Set-Content -Path $defaultsFile -Encoding ASCII
}

$listener = Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($listener) {
    Write-Output "MySQL already listening on 127.0.0.1:3306 (PID $($listener.OwningProcess))"
    exit 0
}

if (-not (Test-Path $errorLog)) {
    & "$mysqlBin\mysqld.exe" --defaults-file="$defaultsFile" --initialize-insecure --console
}

$process = Start-Process `
    -FilePath "$mysqlBin\mysqld.exe" `
    -ArgumentList "--defaults-file=$defaultsFile" `
    -WorkingDirectory $mysqlBin `
    -WindowStyle Hidden `
    -PassThru

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    $listener = Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        Write-Output "MySQL started on 127.0.0.1:3306 (PID $($listener.OwningProcess))"
        exit 0
    }
}

throw "MySQL did not start successfully. Check $errorLog"
