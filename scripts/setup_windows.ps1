$ErrorActionPreference = 'Stop'
$Root = Resolve-Path "$PSScriptRoot\.."

if (-not (Test-Path "$Root\.env")) {
    Copy-Item "$Root\.env.example" "$Root\.env"
    Write-Host "Created .env from .env.example"
}

Set-Location "$Root\backend"
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-dev.txt

Set-Location "$Root\frontend"
npm ci

Write-Host ""
Write-Host "Setup complete."
Write-Host "Terminal 1: powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1"
Write-Host "Terminal 2: powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1"
