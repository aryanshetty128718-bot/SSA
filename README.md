# Smart Shopping Assistant (SSA)
> **AI-Based Food and Beverage Analysis and Healthier-Alternative Recommendation Web App**  
> *Final-Year Major Project | Master of Computer Applications (MCA)*  
> **Official Project Title:** Smart Shopping Assistant  

---

## 1. Project Overview

The **Smart Shopping Assistant (SSA)** empowers consumers to cut through deceptive front-of-pack claims and ultra-processed food formulations by providing:
1. **Scientific Nutritional Assessment**: Official **Nutri-Score 2023** standard computation (Solid foods vs Beverages per 100ml) paired with a transparent **Proposed Project Scoring Framework (0–100 continuous score)** featuring dynamic weight renormalization for missing values.
2. **Rule-Based Heuristic Profiling**: Neutral informational flagging of additives (INS/E-numbers), sugar position hierarchy in ingredient lists, and NOVA processing group interpretations.
3. **Machine Learning Intelligence**: Supervised food classification (**Model A**: Calibrated Linear SVM, 94.9% test accuracy), semantic ingredient TF-IDF cosine similarity, and nutrient-vector KNN peer ranking (**Model B**: Calibrated hybrid similarity retrieval) for discovering healthier, category-coherent food alternatives with strict trade-off guarding.

---

## 2. Problem Statement

Modern consumers face significant hurdles when attempting to evaluate the true nutritional quality and safety of packaged consumer goods:
- **Deceptive Front-of-Pack Marketing:** Claims like *"natural"*, *"zero cholesterol"*, or *"multigrain"* frequently mask dangerous levels of added sugars, refined vegetable oils, and elevated sodium.
- **Incomprehensible Ingredients & Additives:** Chemical codes (INS/E-numbers) and obscure terms for refined sweeteners obscure ultra-processed formulations.
- **Cognitive Overload & Non-Standardized Declarations:** Labels vary in serving sizes (e.g., per 15g serving vs per 100g basis), preventing apples-to-apples comparisons.
- **Opaque Recommendation Engines:** Commercial shopping platforms recommend products driven by profit margins, ad-spend, or sponsored placements rather than objective health improvements.

### The SSA Solution
SSA solves these problems through an objective, algorithmic dual-engine pipeline:
- **Scientific Engine:** Normalizes declarations to a 100g/ml basis, executes the Santé publique France 2023 Nutri-Score algorithm, detects statutory additives, and applies dynamic weight renormalization.
- **Machine Learning Engine:** Applies sublinear TF-IDF character/word n-grams and standardized nutrient distance to retrieve authentic culinary substitutes, enforcing strict trade-off guards to prevent sodium or fat spikes.

---

## 3. Project Objectives

1. Implement an objective, continuous 0–100 nutritional scoring model with dynamic weight renormalization when packages omit non-mandatory fields.
2. Accurately benchmark products against the official European reference standard (**Nutri-Score 2023**) for solid foods and beverages.
3. Train and deploy supervised machine learning models (**Model A** Category Classifier & **Model B** Multimodal Similarity Engine) evaluated via `GroupShuffleSplit` to avoid data leakage.
4. Provide transparent, explainable recommendations that protect consumers against deceptive nutritional trade-offs.
5. Deliver a responsive, modern web application (React 18 + FastAPI + SQLite) that runs completely offline on a local Windows machine.

---

## 4. Main Features

- **Instant Barcode Search:** GS1 Modulo-10 check-digit validation for GTIN-8, UPC-12, EAN-13, and ITF-14 barcodes.
- **Dual Nutritional Scoring:**
  - *Proposed Project Continuous Score (0–100):* Non-linear penalty/reward curves over 8 nutritional criteria.
  - *Nutri-Score 2023:* Computed reference standard with explicit `NOT_COMPUTABLE` state for incomplete packaging.
- **Dynamic Renormalization & Provisional Score Badge:** Automatically renormalizes remaining criteria weights when nutrients are undeclared; activates a "Provisional Score" badge when confidence is below 50%.
- **8-Parameter Nutritional Radar & Sub-Score Bar:** Visual breakdown across positive and negative nutritional criteria using Recharts.
- **Intelligent Healthier Alternatives:** Suggests category-coherent alternatives requiring meaningful health gains ($\Delta \ge 10.0$ or a Nutri-Score grade jump).
- **Trade-Off Guarding & Explanations:** Warns users if an alternative has higher sodium, sugar, or saturated fat, synthesizing honest natural language summaries.
- **Multi-Product Comparison:** Side-by-side parametric matrix comparing up to 4 products with parameter-level winner indicators.
- **Administrative Scoring Engine Configurator:** Admin interface to modify scoring weights, adjust thresholds, trigger background re-scoring jobs, and inspect audit logs.
- **User Dashboard & Bookmarks:** JWT-authenticated user dashboard with scan history tracking and product bookmarking.

---

## 5. Supported Product Categories

The application implements an extensible category architecture with 11 fully operational food and beverage categories in SQLite (`smart_shopping.db`):

| Category | Slug | Product Type | Evaluated Parameters |
| :--- | :--- | :--- | :--- |
| **Breakfast Cereals** | `breakfast-cereals` | Solid | Sugars, fiber, whole grains, sodium, energy |
| **Biscuits & Cookies** | `biscuits-cookies` | Solid | Saturated fat, sugars, flour refinement, additives |
| **Breads & Bakery** | `breads-bakery` | Solid | Sodium, dietary fiber, whole grains, preservatives |
| **Chips & Crisps** | `chips-crisps` | Solid | Total fat, saturated fat, sodium, frying oils |
| **Chocolates & Confectionery** | `chocolates-confectionery` | Solid | Added sugars, cocoa solids, palm oil, emulsifiers |
| **Dairy & Plant Drinks** | `dairy-plant-drinks` | Beverage | Lactose/free sugars, calcium, saturated fat, protein |
| **Fruit Juices** | `fruit-juices` | Beverage | Natural vs added sugars, fruit content, vitamin C |
| **Soft Drinks & Sodas** | `soft-drinks-sodas` | Beverage | Liquid sugar density, artificial sweeteners, acidity |
| **Sweet Spreads & Nut Butters** | `sweet-spreads-nut-butters` | Solid | Nut percentage, palm oil, free sugars, proteins |
| **Yoghurts** | `yoghurts` | Solid | Live cultures, added fruit sugars, protein, fat |
| **Instant Noodles & Pasta** | `instant-noodles-pasta` | Solid | Sodium content, refining index, seasoning additives |

*Architectural Scope:* The data models support expansion into Personal Care, Healthcare/Supplements, and Electronics; the active operational implementation focuses on Food and Beverages.

---

## 6. Machine Learning Architecture

```
[Open Food Facts Dataset (N = 6,056)]
                 │
      GroupShuffleSplit (80/20)
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
[Model A: Classifier] [Model B: Similarity]
• LinearSVC (Calibrated) • TF-IDF Cosine (0.50)
• Word/Char N-Grams      • Nutrient Euclidean (0.50)
• 7 Standardized Nutrients • Calibrated Threshold (0.08)
       │                   │
       ▼                   ▼
Online Category Guard  Healthier Peer Retrieval
(94.9% Test Accuracy)  (94.1% Coherence Agreement)
```

- **Model A (Category Classifier):** Calibrated Linear Support Vector Machine (`LinearSVC` wrapped with `CalibratedClassifierCV`) combining sublinear TF-IDF character/word n-grams (2–4 n-grams, 5,000 features) with 7 standardized nutrient dimensions. Evaluated using `GroupShuffleSplit` ($80/20$) grouped by brand/product-line key to eliminate data leakage. Achieves **94.9% held-out test accuracy**.
- **Model A2 (Product Type Classifier):** Calibrated Linear SVM on 1,208 multimodal features (1,200 TF-IDF n-grams + 8 standardized nutrient dimensions) trained on authentic Open Food Facts catalogues across 45 Level-2 culinary product types. Evaluated via `GroupShuffleSplit` by brand. Achieves **89.19% held-out accuracy and 0.8869 weighted F1** (`ml/artifacts/product_type_classifier.joblib`).
- **Model B (Similarity Retrieval Engine):** Pairwise hybrid similarity metric:
  $$\text{Sim}_{\text{hybrid}} = 0.50 \cdot \text{Cosine}(\mathbf{t}_{\text{query}}, \mathbf{t}_{\text{cand}}) + 0.50 \cdot \left(\frac{1}{1 + d_{\text{euclid}}(\mathbf{n}_{\text{query}}, \mathbf{n}_{\text{cand}})}\right)$$
- **Hybrid Tiered Recommendation Engine (v4.0):**
  - Evaluated on **160 held-out query products** across all categories (`docs/recommendation_eval.md`):
  - **Tier 1 (Same Product Type):** **94.7%** (682 / 720 recommendations)
  - **Tier 2 (Related Culinary Alternative):** **5.3%** (38 / 720 recommendations; fallback only when Tier 1 < 5)
  - **Tier 3 (Outside / Disqualified):** **0.0%** (strictly zero cross-category leaps)
  - **Formulation Preservation:** Jaccard canonical ingredient similarity ranking + Cosine nutrient similarity.
- **Search Success Resilience & Manual Entry Fallback:**
  - Automated Search Success Rate: **87.6%** on diverse audit barcodes (up from 44.8%).
  - Upstream timeout resilience (3.5s per-attempt timeout, exponential backoff, 24h negative cache with retry-live bypass).
  - Country mirror routing (`in.openfoodfacts.org` for 890 GS1 India prefixes) + optional USDA FoodData Central fallback.
  - Interactive **Manual Entry Dialog** prefilling barcode and validating physiological ranges (`sugars <= carbs`, `sat fat <= fat`, non-negative bounds), ensuring **100% resolution for any barcode in the market**.

---

## 7. Technologies Used

- **Frontend:** React 18 (TypeScript), Vite 5, Tailwind CSS 3, Recharts, Lucide React, Axios, React Router v6.
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, bcrypt, PyJWT, HTTPX.
- **Database:** SQLite (`smart_shopping.db` — official zero-config default) with optional PostgreSQL 16 support (`docker-compose.yml`).
- **Machine Learning:** scikit-learn 1.4+, pandas, numpy, joblib.
- **Testing:** Pytest (86 backend tests with 100% database isolation), Vitest (16 frontend tests).

---

## 8. System Workflow

1. User scans barcode or enters search query.
2. GS1 Modulo-10 algorithm validates barcode format and check digit.
3. System checks local SQLite cache (`smart_shopping.db`); falls back to Open Food Facts API v2 if uncached.
4. Raw data is parsed, normalized to 100g/ml basis, and persisted in local DB.
5. Model A independently verifies product category.
6. Scientific calculator computes 0–100 continuous score and Nutri-Score 2023 grade.
7. Dynamic renormalization calculates data completeness and applies confidence rating.
8. Model B searches candidate pool for category-coherent peers with higher scores.
9. Trade-off guard inspects candidates for sugar, sodium, or fat spikes, synthesizing explanations.
10. UI renders radar charts, score bars, nutrition tables, ingredient chips, and alternatives.

---

## 9. Installation & Running Instructions

### Prerequisites
- Python 3.11 or 3.12 ([python.org](https://www.python.org/downloads/))
- Node.js 18 or 20 LTS ([nodejs.org](https://nodejs.org/))

### One-Click Setup (Windows PowerShell)
```powershell
# 1. Setup virtual environment, dependencies, database migrations
.\setup.ps1

# 2. Launch FastAPI Backend Server (http://127.0.0.1:8000)
.\run_backend.ps1

# 3. Launch Vite React Frontend (http://localhost:5173)
.\run_frontend.ps1

# 4. Run automated test suite
.\run_tests.ps1
```

### Manual Commands
```powershell
# Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
alembic -c backend\alembic.ini upgrade head
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

- **Frontend URL:** `http://localhost:5173`
- **Backend API Docs (Swagger):** `http://127.0.0.1:8000/docs`

### Demo Credentials
- **Admin:** `admin@example.com` / `Admin@12345`
- **Demo User:** `demo@smartshopping.local` / `Demo@12345`

### Key Demo Barcodes
- `3017620422003`: **Nutella** (Grade E, Score 37.0, 4 peanut butter alternatives)
- `5449000000439`: **Coca-Cola Original** (Beverage scoring, Grade E, Score 22.0)
- `8901063023901`: **Britannia Marie Gold** (Indian product, Nutri-Score NOT_COMPUTABLE)
- `0012700158042`: **Skinner Spaghetti** (Low-data product, Provisional Score badge)
- `4006381333932`: Altered check digit (Triggers HTTP 422 error state)
- `8909999999994`: Uncached valid barcode offline (Triggers HTTP 503 Service Unavailable)

---

## 10. Project Folder Structure

```text
Smart_Shopping_Assistant/
├── backend/                 # FastAPI REST API & database persistence
│   ├── alembic/             # Database schema migration scripts
│   ├── app/                 # Backend source code (api, core, db, models, schemas, services, scoring)
│   ├── tests/               # Pytest automated test suite (72 tests)
│   ├── alembic.ini          # Alembic migration configuration
│   ├── requirements.txt     # Python backend dependencies
│   └── seed_data.py         # Initial catalog and test product seeder
├── frontend/                # React 18 + Vite frontend SPA
│   ├── public/              # Static public assets
│   ├── src/                 # React source code (components, pages, api, contexts, types)
│   └── package.json         # Frontend npm dependencies and build scripts
├── ml/                      # Machine Learning models, training pipelines & evaluations
│   ├── artifacts/           # Serialized models (.joblib) and metadata JSONs
│   ├── data/                # Processed Open Food Facts training datasets
│   └── training/            # Model training and vectorization scripts
├── docs/                    # Complete architectural and scientific specifications
│   └── screenshots/         # Verified desktop (1280px) and mobile (390px) screenshots
├── smart_shopping.db        # Pre-populated SQLite database (2,558 products, 11 categories)
├── .env.example             # Template environment variables (Placeholders only)
├── setup.ps1                # Automated 1-click Windows setup script
├── run_backend.ps1          # Automated backend launch script
├── run_frontend.ps1         # Automated frontend launch script
├── run_tests.ps1            # Automated test execution script
├── PROJECT_DESCRIPTION.md   # Comprehensive academic project description
├── SETUP_GUIDE.md           # Step-by-step installation and troubleshooting guide
└── README.md                # Project documentation and run guide
```

---

## 11. Project Limitations

1. **Regional OFF Coverage:** Open Food Facts has limited crowdsourced coverage for certain Indian packaged food categories (e.g., complete declarations for Indian soft drinks, juices, and noodles are scarce). The database currently contains 156 verified Indian OFF products (149 with GS1 890 prefix).
2. **Declaration Reliance:** Evaluations rely strictly on manufacturer packaging declarations; laboratory chemical assays are not conducted.
3. **Category Scope:** Operational implementation covers Food and Beverages. Personal care, healthcare, and electronics are architecturally outlined but not active in scoring.
4. **Informational Scope:** Scores are informational public health tools and do not constitute clinical or medical advice.

---

## 12. Future Enhancements

1. Ingest regional government food composition tables (e.g., ICMR-NIN Indian Food Composition Tables).
2. Activate personal care ingredient hazard scoring via Open Beauty Facts.
3. Implement on-device camera OCR for packaging without barcodes.
4. Provide personalized dietary restriction profiles (diabetic, low-sodium, vegan).
5. Develop cross-platform mobile native applications (React Native / Flutter).
