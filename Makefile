.PHONY: help setup seed import retrain run-backend run-frontend test test-backend test-frontend clean

help:
	@echo "Smart Shopping Assistant (SSA) - Academic MCA Project Management"
	@echo "=================================================================="
	@echo "make setup        - Install backend and frontend dependencies"
	@echo "make seed         - Initialize SQLite/PostgreSQL schema and seed demo products"
	@echo "make import       - Harvest real products from Open Food Facts API v2"
	@echo "make retrain      - Retrain Model A (Classifier) & Model B (Similarity)"
	@echo "make run-backend  - Start FastAPI REST API server on http://localhost:8000"
	@echo "make run-frontend - Start React/Vite development server on http://localhost:5173"
	@echo "make test         - Run full automated test suite (backend pytest + frontend vitest)"
	@echo "make clean        - Remove caches and build artifacts"

setup:
	@echo "Installing backend dependencies..."
	pip install -r backend/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

seed:
	@echo "Initializing database and seeding demo products..."
	python backend/seed_data.py

import:
	@echo "Importing products from Open Food Facts..."
	python backend/scripts/import_off_catalog.py

retrain:
	@echo "Retraining ML Category Classifier and Similarity Engine..."
	python ml/training/train_classifier.py
	python ml/training/train_similarity.py

run-backend:
	@echo "Starting FastAPI backend server on http://localhost:8000..."
	python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

run-frontend:
	@echo "Starting React/Vite frontend on http://localhost:5173..."
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	@echo "Running backend pytest test suite..."
	python -m pytest backend/tests/ -v

test-frontend:
	@echo "Running frontend vitest test suite..."
	cd frontend && npm run test

clean:
	@echo "Cleaning temporary files and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf frontend/dist
