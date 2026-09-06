$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RuntimeDirectory = Join-Path $ProjectRoot ".run"
$PidFile = Join-Path $RuntimeDirectory "server.pid"

function Import-ProjectEnv {
    $envFile = Join-Path $ProjectRoot ".env"
    if (-not (Test-Path $envFile)) {
        throw ".env is missing. Run .\scripts\windows\install.ps1 first, then configure .env."
    }

    foreach ($line in Get-Content $envFile) {
        $entry = $line.Trim()
        if (-not $entry -or $entry.StartsWith("#") -or -not $entry.Contains("=")) { continue }
        $key, $value = $entry.Split("=", 2)
        $key = $key.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        if ($key) { Set-Item -Path "Env:$key" -Value $value }
    }
}

function Get-ConfiguredPort {
    if ($env:PORT) { return [int]$env:PORT }
    return 8000
}

function Get-ListeningProcessId([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) { return $listener.OwningProcess }
    return $null
}

function Test-ProjectProcess([int]$ProcessId) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) { return $false }
    return $process.CommandLine -match [regex]::Escape($ProjectRoot) -and $process.CommandLine -match "app\.py"
}
