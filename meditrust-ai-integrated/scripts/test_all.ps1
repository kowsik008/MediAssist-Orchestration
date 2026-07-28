$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = $projectRoot

function Invoke-Checked {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Invoke-Checked "Knowledge tests" {
    & (Join-Path $projectRoot ".venv-knowledge\Scripts\python.exe") -m pytest (Join-Path $projectRoot "knowledge_service\tests") -q
}
Invoke-Checked "Governance tests" {
    & (Join-Path $projectRoot ".venv-governance\Scripts\python.exe") -m pytest (Join-Path $projectRoot "governance_service\tests") -q
}
Invoke-Checked "Orchestration tests" {
    & (Join-Path $projectRoot ".venv-orchestration\Scripts\python.exe") -m pytest (Join-Path $projectRoot "orchestration_service\tests") -q
}
Invoke-Checked "Gateway tests" {
    & (Join-Path $projectRoot ".venv-gateway\Scripts\python.exe") -m pytest (Join-Path $projectRoot "tests\test_gateway_contracts.py") -q
}

Push-Location (Join-Path $projectRoot "frontend")
try {
    Invoke-Checked "Frontend lint" { npm run lint }
    Invoke-Checked "Frontend build" { npm run build }
}
finally {
    Pop-Location
}
