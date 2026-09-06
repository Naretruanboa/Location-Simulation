param(
    [switch]$Follow
)

. "$PSScriptRoot\common.ps1"

$outputLog = Join-Path $RuntimeDirectory "server.log"
$errorLog = Join-Path $RuntimeDirectory "server.error.log"
if (-not (Test-Path $outputLog) -and -not (Test-Path $errorLog)) {
    Write-Host "No server log yet. Run .\scripts\windows\start.ps1 first."
    exit 0
}

if (Test-Path $outputLog) {
    Write-Host "--- server.log ---"
    Get-Content $outputLog -Tail 200
}
if (Test-Path $errorLog -and (Get-Item $errorLog).Length -gt 0) {
    Write-Host "--- server.error.log ---"
    Get-Content $errorLog -Tail 200
}
if ($Follow) {
    if (-not (Test-Path $outputLog)) { New-Item -ItemType File -Path $outputLog | Out-Null }
    Write-Host "Following server.log. Press Ctrl+C to stop."
    Get-Content $outputLog -Tail 50 -Wait
}
