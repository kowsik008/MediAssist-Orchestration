param(
    [switch]$WithHeadroom,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

function Install-PythonService {
    param(
        [string]$EnvironmentName,
        [string]$RequirementsPath
    )

    $venvPath = Join-Path $projectRoot $EnvironmentName
    $pythonPath = Join-Path $venvPath "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        Write-Host "Creating $EnvironmentName"
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create $EnvironmentName"
        }
    }
    Write-Host "Installing $RequirementsPath"
    & $pythonPath -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip for $EnvironmentName"
    }
    & $pythonPath -m pip install --no-compile -r (Join-Path $projectRoot $RequirementsPath)
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install $RequirementsPath"
    }
}

Install-PythonService ".venv-knowledge" "knowledge_service\requirements.txt"
Install-PythonService ".venv-governance" "governance_service\requirements.txt"

$orchestrationRequirements = "orchestration_service\requirements.txt"
if ($WithHeadroom) {
    $orchestrationRequirements = "orchestration_service\requirements-headroom.txt"
}
Install-PythonService ".venv-orchestration" $orchestrationRequirements
Install-PythonService ".venv-gateway" "integration_api\requirements.txt"

if (-not $SkipFrontend) {
    Push-Location (Join-Path $projectRoot "frontend")
    try {
        npm install --legacy-peer-deps --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install frontend dependencies"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host "MediTrust AI setup completed."
