@echo off
echo Starting SSA FastAPI Backend Server on http://localhost:8000...
set PYTHONPATH=backend
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
