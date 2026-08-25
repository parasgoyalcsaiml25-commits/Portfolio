# Stop AI Resume Portfolio Generator Backend
$ErrorActionPreference = "SilentlyContinue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Stopping AI Resume Portfolio Generator Backend..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$conns = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($conns) {
    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($p in $pids) {
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        Write-Host "[v] Successfully stopped backend server (PID $p)." -ForegroundColor Green
    }
} else {
    Write-Host "[*] No server process found listening on port 5000." -ForegroundColor Yellow
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Shutdown complete." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
