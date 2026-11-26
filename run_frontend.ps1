# Start Vite Frontend Server
Write-Host "Starting SSA Vite React Frontend on http://127.0.0.1:5173..." -ForegroundColor Cyan

Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
Set-Location ..
