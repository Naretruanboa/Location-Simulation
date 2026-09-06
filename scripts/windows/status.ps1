. "$PSScriptRoot\common.ps1"
Import-ProjectEnv

$port = Get-ConfiguredPort
$processId = Get-ListeningProcessId $port
if ($processId) {
    Write-Host "Server is running on port $port (PID $processId)"
} else {
    Write-Host "Server is stopped"
}
