. "$PSScriptRoot\common.ps1"
Import-ProjectEnv

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment is missing. Run .\scripts\windows\install.ps1" }

$port = Get-ConfiguredPort
$existingPid = Get-ListeningProcessId $port
if ($existingPid) {
    Write-Host "Server is already running on port $port (PID $existingPid)"
    exit 0
}

New-Item -ItemType Directory -Force -Path $RuntimeDirectory | Out-Null
$process = Start-Process -FilePath $python -ArgumentList "app.py" -WorkingDirectory $ProjectRoot -PassThru `
    -RedirectStandardOutput (Join-Path $RuntimeDirectory "server.log") `
    -RedirectStandardError (Join-Path $RuntimeDirectory "server.error.log")
Set-Content -Path $PidFile -Value $process.Id
Write-Host "Server started (PID $($process.Id)). Open http://127.0.0.1:$port"
