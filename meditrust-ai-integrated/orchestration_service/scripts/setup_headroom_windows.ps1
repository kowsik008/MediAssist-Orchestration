param(
    [switch]$SkipInstall,
    [switch]$StartProxy,
    [int]$ProxyPort = 8787
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[headroom-setup] $Message"
}

function Fail-Step {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

function Resolve-ServiceRoot {
    return Split-Path -Parent $PSScriptRoot
}

function Resolve-VenvPython {
    param([string]$ServiceRoot)
    $python = Join-Path $ServiceRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        Fail-Step "Virtual environment python was not found at $python"
    }
    return $python
}

function Find-CargoBin {
    $candidates = @(
        (Join-Path $env:USERPROFILE ".cargo\bin"),
        (Join-Path $env:LOCALAPPDATA "puccinialin\puccinialin\Cache\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path (Join-Path $candidate "cargo.exe"))) {
            return $candidate
        }
    }
    return $null
}

function Find-LinkerBin {
    $roots = @(
        "C:\Program Files\Microsoft Visual Studio",
        "C:\Program Files (x86)\Microsoft Visual Studio"
    )

    foreach ($root in $roots) {
        if (Test-Path $root) {
            $match = Get-ChildItem $root -Recurse -Filter link.exe -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -match "\\VC\\Tools\\MSVC\\" } |
                Select-Object -First 1
            if ($match) {
                return $match.DirectoryName
            }
        }
    }

    return $null
}

function Add-ToPathIfMissing {
    param(
        [string]$PathToAdd
    )

    if (-not $PathToAdd) {
        return
    }

    $currentPaths = $env:PATH -split ";"
    if ($currentPaths -notcontains $PathToAdd) {
        $env:PATH = "$PathToAdd;$env:PATH"
    }
}

function Assert-Prereqs {
    $cargoBin = Find-CargoBin
    if (-not $cargoBin) {
        Fail-Step "Rust/Cargo was not found. Install Rust before setting up Headroom."
    }
    Add-ToPathIfMissing -PathToAdd $cargoBin
    Write-Step "Cargo found at $cargoBin"

    $linkerBin = Find-LinkerBin
    if (-not $linkerBin) {
        Fail-Step "Microsoft C++ Build Tools linker (link.exe) was not found. Install Visual Studio Build Tools with Desktop development with C++."
    }
    Add-ToPathIfMissing -PathToAdd $linkerBin
    Write-Step "MSVC linker found at $linkerBin"
}

function Install-Headroom {
    param(
        [string]$PythonExe
    )
    Write-Step "Installing headroom-ai[proxy] into the service virtual environment"
    & $PythonExe -m pip install "headroom-ai[proxy]"
    if ($LASTEXITCODE -ne 0) {
        Fail-Step "Headroom installation failed."
    }
}

function Write-EnvFile {
    param(
        [string]$ServiceRoot,
        [int]$Port
    )

    $envPath = Join-Path $ServiceRoot ".env"
    if (-not (Test-Path $envPath)) {
        Fail-Step "Expected .env file at $envPath"
    }

    $content = Get-Content $envPath -Raw
    $content = [regex]::Replace($content, "(?m)^HEADROOM_ENABLED=.*$", "HEADROOM_ENABLED=true")
    $content = [regex]::Replace($content, "(?m)^HEADROOM_AVAILABLE=.*$", "HEADROOM_AVAILABLE=true")
    $content = [regex]::Replace($content, "(?m)^HEADROOM_BASE_URL=.*$", "HEADROOM_BASE_URL=http://127.0.0.1:$Port")
    $content = [regex]::Replace($content, "(?m)^HEADROOM_PROXY_PORT=.*$", "HEADROOM_PROXY_PORT=$Port")
    Set-Content -Path $envPath -Value $content -Encoding UTF8
    Write-Step "Updated .env for Headroom proxy on port $Port"
}

function Start-HeadroomProxy {
    param(
        [string]$PythonExe,
        [string]$ServiceRoot,
        [int]$Port
    )

    Write-Step "Starting Headroom proxy on 127.0.0.1:$Port"
    Start-Process `
        -FilePath $PythonExe `
        -ArgumentList "-m", "headroom.cli", "proxy", "--host", "127.0.0.1", "--port", "$Port" `
        -WorkingDirectory $ServiceRoot `
        -WindowStyle Hidden | Out-Null

    Start-Sleep -Seconds 5
    try {
        $health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/health"
        Write-Step "Proxy health: $($health.Content)"
    }
    catch {
        Fail-Step "Headroom proxy did not become healthy on port $Port"
    }
}

$serviceRoot = Resolve-ServiceRoot
$venvPython = Resolve-VenvPython -ServiceRoot $serviceRoot

Assert-Prereqs

if (-not $SkipInstall) {
    Install-Headroom -PythonExe $venvPython
}

Write-EnvFile -ServiceRoot $serviceRoot -Port $ProxyPort

if ($StartProxy) {
    Start-HeadroomProxy -PythonExe $venvPython -ServiceRoot $serviceRoot -Port $ProxyPort
}

Write-Step "Windows-native Headroom setup completed."
