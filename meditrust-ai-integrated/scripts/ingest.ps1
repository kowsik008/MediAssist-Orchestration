$ErrorActionPreference = "Stop"
$body = @{ reset = $true } | ConvertTo-Json
$response = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8001/ingest" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
$response | ConvertTo-Json -Depth 5
