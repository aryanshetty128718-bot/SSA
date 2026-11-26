# Start FastAPI Backend Server
Write-Host "Starting SSA FastAPI Backend Server on http://127.0.0.1:8000..." -ForegroundColor Cyan

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
