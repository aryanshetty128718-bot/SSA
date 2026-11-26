# Setup and Installation Guide: Smart Shopping Assistant (SSA)
> **Academic Final-Year Major Project | Master of Computer Applications (MCA)**  
> **Official Project Title:** Smart Shopping Assistant  
> **Target Environment:** Local Machine Demonstration (Windows 10/11, macOS, Linux)  

---

## 1. System Requirements & Prerequisites

The Smart Shopping Assistant is engineered to execute locally without mandatory cloud services, external API keys, or Docker dependencies.

### Hardware Requirements
- **Processor:** Intel Core i3 / AMD Ryzen 3 or higher (Dual-Core 2.0 GHz minimum)
- **RAM:** 4 GB minimum (8 GB recommended for simultaneous browser and ML inference)
- **Storage:** 2 GB available disk space (including Python virtual environment, dependencies, and SQLite database)
- **Operating System:** Windows 10/11 (64-bit), macOS 12+, or Ubuntu Linux 20.04+

### Required Software & Versions
| Software | Required Version | Verification Command | Download URL |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11.x or 3.12.x (3.12 recommended) | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18.x or 20.x LTS | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | 9.x or 10.x | `npm --version` | Bundled with Node.js |
| **PowerShell** | 5.1+ (Windows Default) | `$PSVersionTable.PSVersion` | Built into Windows |
| **Modern Web Browser** | Chrome, Edge, Firefox, or Safari | Latest stable | N/A |

> [!IMPORTANT]
> When installing Python on Windows, ensure you check the box: **"Add python.exe to PATH"** on the first installer screen.

---

## 2. Project Extraction Instructions

1. Locate the submission archive: `Smart_Shopping_Assistant.zip`.
2. Extract the archive into a clean directory of your choice (e.g., `C:\Projects\Smart_Shopping_Assistant` or `~/projects/Smart_Shopping_Assistant`).
3. Ensure the directory path does not contain special characters or spaces where possible.
4. Open **PowerShell** (on Windows) or **Terminal** (on macOS/Linux) and navigate to the extracted root directory:
   ```powershell
   cd path\to\Smart_Shopping_Assistant
   ```

---

## 3. Directory Structure Overview

Ensure the following core structure is present in your extracted directory:

```text
Smart_Shopping_Assistant/
├── backend/                 # FastAPI REST API & database persistence
│   ├── alembic/             # Database schema migration scripts
│   ├── app/                 # Backend source code (api, core, db, models, schemas, services, scoring)
│   ├── tests/               # Pytest automated test suite (72 unit & integration tests)
│   ├── alembic.ini          # Alembic migration configuration
│   ├── requirements.txt     # Python backend dependencies
│   └── seed_data.py         # Initial catalog and test product seeder
├── frontend/                # React 18 + Vite frontend Single Page Application
│   ├── public/              # Static public assets
│   ├── src/                 # React source code (components, pages, api, contexts, types)
│   └── package.json         # Frontend npm dependencies and build scripts
├── ml/                      # Machine Learning models, training pipelines & evaluations
│   ├── artifacts/           # Serialized model binaries (.joblib) and metadata JSONs
│   ├── data/                # Processed Open Food Facts training datasets
│   └── training/            # Model training and vectorization scripts
├── docs/                    # Complete architectural and scientific specifications
│   └── screenshots/         # Verified desktop (1280px) and mobile (390px) screenshots
├── smart_shopping.db        # Pre-populated SQLite database (2,558 products, 11 categories)
├── .env.example             # Template environment variables (Placeholders only)
├── setup.ps1                # Automated 1-click Windows setup script
├── run_backend.ps1          # Automated backend launch script
├── run_frontend.ps1         # Automated frontend launch script
└── run_tests.ps1            # Automated test execution script
```

---

## 4. Quick Start (Windows PowerShell - Recommended)

For instantaneous setup and execution on Windows machines, use the provided PowerShell automation scripts:

```powershell
# Step 1: Execute complete automated setup (virtual environment, dependencies, DB verify)
.\setup.ps1

# Step 2: Open a new terminal window and launch the FastAPI Backend server
.\run_backend.ps1

# Step 3: Open another terminal window and launch the Vite React Frontend
.\run_frontend.ps1

# Step 4: Open your web browser and navigate to:
# http://localhost:5173
```

---

## 5. Step-by-Step Manual Installation

If you prefer to configure the environment manually or are running on macOS/Linux:

### Step 5.1: Environment Variable Configuration
Copy the template `.env.example` to create `.env`:
```powershell
# Windows PowerShell:
Copy-Item ".env.example" ".env"

# macOS / Linux Bash:
cp .env.example .env
```

**Understanding `.env`:**
The pre-configured `.env` works out of the box with the default SQLite database:
```env
ENVIRONMENT=development
DEBUG=True
APP_NAME="Smart Shopping Assistant"
API_V1_PREFIX=/api/v1
SECRET_KEY=super-secret-key-mca-project-2026-development-eval-only
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Official Default SQLite Database
DATABASE_URL=sqlite:///./smart_shopping.db

# Open Food Facts API
OPEN_FOOD_FACTS_BASE_URL=https://world.openfoodfacts.org
OPEN_FOOD_FACTS_TIMEOUT_SECONDS=8.0
USER_AGENT="SmartShoppingAssistant/1.0 (Academic MCA Project)"

# CORS Allowed Origins
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```
> [!NOTE]
> The project includes a fully pre-populated SQLite database (`smart_shopping.db`). You do **not** need to install PostgreSQL or Docker for your academic demonstration.

---

### Step 5.2: Backend Setup & Dependency Installation

1. Create and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux Bash:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Upgrade `pip` and install backend dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

3. Verify Database Migrations:
   ```bash
   alembic -c backend/alembic.ini upgrade head
   ```

4. Verify Machine Learning Artifacts:
   Ensure that the serialized models exist in `ml/artifacts/`:
   - `category_classifier.joblib` (Model A - 1.5 MB)
   - `similarity_engine.joblib` (Model B - 6.6 MB)
   *(These are pre-trained and included in the project package. If missing, they can be regenerated by running `python ml/training/train_classifier.py` and `python ml/training/train_similarity.py`).*

---

### Step 5.3: Frontend Setup & Dependency Installation

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies using `npm`:
   ```bash
   npm install
   ```

3. Return to the root directory:
   ```bash
   cd ..
   ```

---

## 6. Running the Application

### 6.1 Start the Backend Server
From the project root directory (with `.venv` activated):
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
- **Alternative ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **Health Check Endpoint:** `http://127.0.0.1:8000/api/v1/health`

### 6.2 Start the Frontend Development Server
In a separate terminal window, navigate to `frontend` and start Vite:
```bash
cd frontend
npm run dev
```
- **Frontend Application URL:** `http://localhost:5173` (or `http://127.0.0.1:5173`)

---

## 7. Demo Accounts & Credentials

The pre-populated database includes pre-configured administrative and standard demonstration accounts:

| Role | Email Address | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@example.com` | `Admin@12345` | System Metrics, Product CRUD, Scoring Criteria Configuration, Background Re-scoring, Audit Logs |
| **Demo User** | `demo@smartshopping.local` | `Demo@12345` | Product Analysis, History Inspection, Bookmarking & Saved Products |

> [!TIP]
> You can also click **"Create Account"** on the login page to register a new user profile at any time.

---

## 8. Key Demonstration Barcodes

Test the application during your academic viva using these verified demonstration barcodes:

| Barcode | Product Name | Brand | Demonstration Significance |
| :--- | :--- | :--- | :--- |
| `3017620422003` | **Nutella** (Hazelnut & Cocoa Spread) | Ferrero | High sugar & saturated fat, Grade E, retrieves 4 healthier alternatives (Peanut Butter) with trade-off flags |
| `5449000000439` | **Coca-Cola Original Taste** | Coca-Cola | Beverage scoring (per 100ml), severe sugar penalty ($10.6\text{g}$), retrieves sparkling water & lemon alternatives |
| `8901063023901` | **Britannia Marie Gold Biscuits** | Britannia | Real Indian product, fiber not declared on package ($p_{\text{fiber}}=\text{None}$), Nutri-Score `NOT_COMPUTABLE` |
| `0012700158042` | **Skinner Spaghetti** | New World Pasta | Low-data product ($C = 0.42$), missing sugars/sodium, triggers **Provisional Score** badge in UI |
| `4006381333932` | *(Altered Check Digit)* | N/A | Invalid check-digit test (Expected 1, got 2); triggers **HTTP 422** error state in UI |
| `8909999999994` | *(Uncached Valid Barcode)* | N/A | Offline mode verification; returns **HTTP 503 Service Unavailable** when network is disconnected |

---

## 9. Running Automated Tests

The project includes automated test suites covering backend API routes, scientific calculations, and frontend components:

### Backend Test Suite (Pytest)
From the project root:
```bash
python -m pytest backend/tests/ -v
```
*Expected Result:* **72 passed** (covers authentication, barcode validation, scoring boundaries, Nutri-Score 2023, near-duplicates, trade-off guarding, and admin endpoints).

### Frontend Test Suite (Vitest)
From the `frontend` directory:
```bash
cd frontend
npm test
```
*Expected Result:* **16 passed** across 3 test suites (`barcodeValidator.test.ts`, `DeltaChip.test.tsx`, `ScoreGauge.test.tsx`).

---

## 10. Common Installation Errors & Troubleshooting

### 1. `Execution of scripts is disabled on this system` (PowerShell)
- **Cause:** Windows PowerShell execution policy restricts script execution by default.
- **Solution:** Open PowerShell as Administrator and run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
  Or run the scripts bypassing the policy directly:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\setup.ps1
  ```

### 2. `python` or `pip` is not recognized as an internal or external command
- **Cause:** Python was installed without checking the "Add Python to PATH" option.
- **Solution:** Re-run the Python installer, select **Modify**, and check the box to add Python to the environment variables. Alternatively, reference the full path (e.g., `C:\Users\<User>\AppData\Local\Programs\Python\Python312\python.exe`).

### 3. `Port 8000 or Port 5173 is already in use`
- **Cause:** A previous instance of uvicorn or vite is still running in the background.
- **Solution:** Terminate the occupying process or run on an alternate port:
  ```powershell
  # To find and kill process on port 8000:
  netstat -ano | findstr :8000
  taskkill /PID <PID_NUMBER> /F
  ```

### 4. `sqlite3.OperationalError: no such table`
- **Cause:** SQLite database file was not initialized or Alembic migrations were not executed.
- **Solution:** Run the database migration command from the root directory:
  ```powershell
  alembic -c backend\alembic.ini upgrade head
  ```

### 5. `ERR_CONNECTION_REFUSED` in Frontend
- **Cause:** The Vite frontend is running, but the FastAPI backend server has not been started.
- **Solution:** Ensure the backend terminal is active and displaying `Application startup complete` on `http://127.0.0.1:8000`.

---

## 11. Security & Production Deployment Notice

- The default database configuration uses local SQLite (`smart_shopping.db`) for academic viva demonstration.
- To use PostgreSQL, spin up the included `docker-compose.yml` (`docker compose up -d`) and update `DATABASE_URL` in `.env`.
- Before any potential production deployment, replace `SECRET_KEY` in `.env` with a cryptographically secure random string:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- **Never commit `.env` containing sensitive credentials to public version control repositories.**
