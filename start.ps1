# AI Resume Portfolio Generator - PowerShell Launcher
$ErrorActionPreference = "SilentlyContinue"
$projectDir = $PSScriptRoot
if (-not $projectDir) { $projectDir = (Get-Location).Path }
Set-Location -Path $projectDir

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI Resume Portfolio Generator Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check if backend is already running on port 5000
Write-Host "[*] Checking if Flask backend is running on port 5000..." -ForegroundColor Gray
$isListening = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("127.0.0.1", 5000)
    $isListening = $true
    $tcp.Dispose()
} catch {
    $isListening = $false
}

if ($isListening) {
    Write-Host "[v] Flask backend is already active on http://127.0.0.1:5000" -ForegroundColor Green
} else {
    Write-Host "[*] Starting Flask backend server (main.py) in the background..." -ForegroundColor Yellow
    
    $venvPythonW = Join-Path $projectDir "venv\Scripts\pythonw.exe"
    $venvPython = Join-Path $projectDir "venv\Scripts\python.exe"
    if (Test-Path $venvPythonW) {
        $pythonCmd = $venvPythonW
    } elseif (Test-Path $venvPython) {
        $pythonCmd = $venvPython
    } else {
        $pythonCmd = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
        if (-not $pythonCmd) {
            $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Source
        }
    }
    
    $mainScript = Join-Path $projectDir "main.py"
    $cmdLine = "`"$pythonCmd`" `"$mainScript`""

    # Use WMI Process Create to detach completely from parent console / job
    $res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $cmdLine
        CurrentDirectory = $projectDir
    }

    # Fallback to Start-Process if CIM is restricted
    if ($res.ReturnValue -ne 0) {
        Start-Process -FilePath $pythonCmd -ArgumentList "`"$mainScript`"" -WorkingDirectory $projectDir -WindowStyle Hidden
    }

    # Wait for backend health check
    Write-Host "[*] Waiting for backend /health endpoint to respond..." -ForegroundColor Gray
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $resp = Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -TimeoutSec 1
            if ($resp.status -eq "healthy") {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 350
        }
    }

    if ($ready) {
        Write-Host "[v] Backend server is active and healthy!" -ForegroundColor Green
    } else {
        Write-Host "[!] Warning: Backend health check took longer than expected." -ForegroundColor DarkYellow
    }
}

# Launch frontend in default browser
$frontendFile = Join-Path $projectDir "index.html"
Write-Host "[*] Opening Portfolio Generator frontend ($frontendFile)..." -ForegroundColor Cyan
Start-Process $frontendFile

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Frontend is ready! Backend API active on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
