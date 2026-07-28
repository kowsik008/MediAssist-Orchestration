param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $projectRoot "logs"
$runDir = Join-Path $projectRoot "run"
New-Item -ItemType Directory -Force -Path $logDir, $runDir | Out-Null

$env:PYTHONPATH = $projectRoot

function Start-Backend {
    param(
        [string]$Name,
        [string]$PythonPath,
        [string]$Module,
        [int]$Port
    )

    $process = Start-Process `
        -FilePath $PythonPath `
        -ArgumentList "-m", "uvicorn", $Module, "--host", "127.0.0.1", "--port", "$Port" `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "$Name.out.log") `
        -RedirectStandardError (Join-Path $logDir "$Name.err.log") `
        -PassThru
    return @{ name = $Name; id = $process.Id; port = $Port }
}

$processes = @()
$processes += Start-Backend "knowledge" (Join-Path $projectRoot ".venv-knowledge\Scripts\python.exe") "knowledge_service.app:app" 8001
$processes += Start-Backend "governance" (Join-Path $projectRoot ".venv-governance\Scripts\python.exe") "governance_service.app.main:app" 8002
$processes += Start-Backend "orchestration" (Join-Path $projectRoot ".venv-orchestration\Scripts\python.exe") "orchestration_service.main:app" 8003
$processes += Start-Backend "gateway" (Join-Path $projectRoot ".venv-gateway\Scripts\python.exe") "integration_api.main:app" 8000

if (-not $SkipFrontend) {
    $frontend = Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000" `
        -WorkingDirectory (Join-Path $projectRoot "frontend") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "frontend.out.log") `
        -RedirectStandardError (Join-Path $logDir "frontend.err.log") `
        -PassThru
    $processes += @{ name = "frontend"; id = $frontend.Id; port = 3000 }
}

$processes | ConvertTo-Json | Set-Content -Path (Join-Path $runDir "pids.json") -Encoding UTF8
Start-Sleep -Seconds 10
& (Join-Path $PSScriptRoot "health_check.ps1")
