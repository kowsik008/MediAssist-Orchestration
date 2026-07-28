$ErrorActionPreference = "Continue"

$checks = @(
    @{ name = "Gateway"; url = "http://127.0.0.1:8000/api/v1/health" },
    @{ name = "Knowledge"; url = "http://127.0.0.1:8001/health" },
    @{ name = "Governance"; url = "http://127.0.0.1:8002/api/v1/health" },
    @{ name = "Orchestration"; url = "http://127.0.0.1:8003/health" },
    @{ name = "Frontend"; url = "http://127.0.0.1:3000" }
)

$failed = $false
foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $check.url -TimeoutSec 5
        Write-Host "$($check.name): OK ($($response.StatusCode))"
    }
    catch {
        $failed = $true
        Write-Host "$($check.name): UNAVAILABLE"
    }
}

if ($failed) {
    exit 1
}
