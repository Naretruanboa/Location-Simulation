. "$PSScriptRoot\common.ps1"

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        & $launcher.Source -3.11 -m venv (Join-Path $ProjectRoot ".venv")
    } else {
        & python -m venv (Join-Path $ProjectRoot ".venv")
    }
}

& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")

$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $ProjectRoot ".env.example") $envFile
    Write-Host "Created .env from .env.example. Configure GPS_PROVIDER and ADB settings before starting."
}
