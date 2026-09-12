$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\backend"
if (Test-Path ".venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} else {
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}
