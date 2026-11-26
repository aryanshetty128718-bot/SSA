@echo off
echo ========================================================
echo Smart Shopping Assistant (SSA) - Windows Setup Script
echo ========================================================

echo [1/3] Installing Python backend dependencies...
python -m pip install -r backend\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Backend dependency installation failed.
    exit /b %ERRORLEVEL%
)

echo [2/3] Installing React frontend dependencies...
cd frontend
call npm install
cd ..

echo [3/3] Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo Created .env from .env.example
)

echo ========================================================
echo Setup complete. Run 'scripts\run_backend.bat' and 'scripts\run_frontend.bat'
echo ========================================================
