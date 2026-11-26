@echo off
echo ========================================================
echo Running Full Automated Test Suite (Backend + Frontend)
echo ========================================================

echo [1/2] Executing backend Pytest suite...
set PYTHONPATH=backend
python -m pytest backend\tests -v
if %ERRORLEVEL% NEQ 0 (
    echo Backend tests failed!
    exit /b %ERRORLEVEL%
)

echo [2/2] Executing frontend Vitest suite...
cd frontend
call npm run test
cd ..

echo ========================================================
echo All backend and frontend test suites passed successfully!
echo ========================================================
