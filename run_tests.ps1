# Run All SSA Automated Test Suites (Backend Pytest + Frontend Vitest)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Running SSA Test Suites (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

Write-Host "`n[1/2] Running Backend Pytest Suite..." -ForegroundColor Yellow
python -m pytest backend/tests/ -v

$backendExit = $LASTEXITCODE

Write-Host "`n[2/2] Running Frontend Vitest Suite..." -ForegroundColor Yellow
Set-Location frontend
npm.cmd run test
$frontendExit = $LASTEXITCODE
Set-Location ..

Write-Host "`n==========================================================" -ForegroundColor Cyan
if ($backendExit -eq 0 -and $frontendExit -eq 0) {
    Write-Host "  ALL TESTS PASSED SUCCESSFULLY (100% Pass Rate)!" -ForegroundColor Green
} else {
    Write-Host "  TEST FAILURES DETECTED! (Backend: $backendExit, Frontend: $frontendExit)" -ForegroundColor Red
}
Write-Host "==========================================================" -ForegroundColor Cyan
