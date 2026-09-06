. "$PSScriptRoot\common.ps1"
Import-ProjectEnv

$port = Get-ConfiguredPort
$processId = Get-ListeningProcessId $port
if (-not $processId) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Server is already stopped"
    exit 0
}
if (-not (Test-ProjectProcess $processId)) {
    throw "Refusing to stop PID $processId because it is not this project's app.py"
}

try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$port/api/location/clear" | Out-Null } catch {}
Stop-Process -Id $processId
Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Write-Host "Stopping server (PID $processId)"
