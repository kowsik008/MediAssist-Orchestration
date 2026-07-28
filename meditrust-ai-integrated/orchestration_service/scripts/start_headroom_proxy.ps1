param(
    [int]$ProxyPort = 8787
)

$ErrorActionPreference = "Stop"
$serviceRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $serviceRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Virtual environment python was not found at $pythonExe"
    exit 1
}

Start-Process `
    -FilePath $pythonExe `
    -ArgumentList "-m", "headroom.cli", "proxy", "--host", "127.0.0.1", "--port", "$ProxyPort" `
    -WorkingDirectory $serviceRoot `
    -WindowStyle Hidden

Write-Host "Headroom proxy launch requested on http://127.0.0.1:$ProxyPort"
