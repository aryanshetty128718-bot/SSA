# Smart Shopping Assistant (SSA) - Local Machine Setup Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Smart Shopping Assistant (SSA) - Local Setup Script" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Environment file
if (-not (Test-Path ".env")) {
    Write-Host "[1/6] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  -> .env created with SQLite default database." -ForegroundColor Green
} else {
    Write-Host "[1/6] .env already exists." -ForegroundColor Green
}

# 2. Python Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "[2/6] Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
}
Write-Host "  -> Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# 3. Python Dependencies
Write-Host "[3/6] Installing backend dependencies..." -ForegroundColor Yellow
pip install -r backend\requirements.txt

# 4. Database Migrations & Seeding
Write-Host "[4/6] Running Alembic database migrations..." -ForegroundColor Yellow
alembic -c backend\alembic.ini upgrade head

Write-Host "  -> Verifying initial seed data..." -ForegroundColor Yellow
python backend\seed_data.py

# 5. ML Artifacts Check
Write-Host "[5/6] Checking ML model artifacts..." -ForegroundColor Yellow
if (-not (Test-Path "ml\artifacts\category_classifier.joblib")) {
    Write-Host "  -> ML artifacts not found. Training models offline..." -ForegroundColor Yellow
    python ml\training\train_all.py
} else {
    Write-Host "  -> ML artifacts present and verified." -ForegroundColor Green
}

# 6. Frontend Setup
Write-Host "[6/6] Installing frontend npm dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm.cmd install
Set-Location ..

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Setup Complete! The application is ready for local demo." -ForegroundColor Green
Write-Host "  - To start backend:  .\run_backend.ps1" -ForegroundColor Cyan
Write-Host "  - To start frontend: .\run_frontend.ps1" -ForegroundColor Cyan
Write-Host "  - To run tests:      .\run_tests.ps1" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
