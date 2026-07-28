$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot "run\pids.json"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "No managed MediTrust AI processes were recorded."
    exit 0
}

$entries = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
foreach ($entry in @($entries)) {
    $process = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $entry.id -Force
        Write-Host "Stopped $($entry.name) (PID $($entry.id))"
    }
}

Remove-Item -LiteralPath $pidFile -Force
