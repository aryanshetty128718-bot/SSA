# 02. Module-Wise Breakdown

## 1. Monorepo File & Directory Layout

The codebase follows a strictly separated monorepo architecture:

```text
smart-shopping-assistant/
├── docs/                                  # Comprehensive architectural and scientific documentation
│   ├── 01_SYSTEM_ARCHITECTURE.md
│   ├── 02_MODULE_WISE_BREAKDOWN.md
│   ├── 03_DATABASE_SCHEMA.md
│   ├── 04_ML_IMPLEMENTATION_STRATEGY.md
│   ├── 05_NUTRITIONAL_SCORING_METHODOLOGY.md
│   ├── 06_API_INTEGRATION_STRATEGY.md
│   └── 07_FRONTEND_ARCHITECTURE.md
├── backend/
│   ├── app/
│   │   ├── api/                           # API Controllers / Route Handlers (NO ML/Scoring logic here)
│   │   │   ├── v1/
│   │   │   │   ├── auth.py                # User login, registration, JWT tokens
│   │   │   │   ├── products.py            # Product retrieval, browsing, CRUD
│   │   │   │   ├── search.py              # Barcode & text search, OFF caching trigger
│   │   │   │   ├── analysis.py            # Analytical breakdown (Nutri-Score, 0-100 score)
│   │   │   │   ├── recommendations.py     # Alternative product recommendation endpoints
│   │   │   │   ├── comparison.py          # Multi-product side-by-side comparison
│   │   │   │   └── admin.py               # Scoring criteria management & system status
│   │   │   └── deps.py                    # Database session and security dependencies
│   │   ├── core/                          # Core configuration and security
│   │   │   ├── config.py                  # Pydantic BaseSettings, env variable management
│   │   │   ├── security.py                # JWT creation, verification, password hashing
│   │   │   └── exceptions.py              # Custom domain and HTTP exception handlers
│   │   ├── db/                            # Database setup
│   │   │   ├── session.py                 # SQLAlchemy engine, sessionmaker, SQLite/Postgres switch
│   │   │   └── base.py                    # Declarative base model registry
│   │   ├── models/                        # SQLAlchemy ORM Models (Normalized relational entities)
│   │   │   ├── user.py                    # Users table
│   │   │   ├── category.py                # Categories hierarchy
│   │   │   ├── product.py                 # Products core table
│   │   │   ├── nutrition.py               # NutritionalInformation table
│   │   │   ├── ingredient.py              # Ingredients & ProductIngredients join table
│   │   │   ├── score.py                   # ProductScores table (precomputed/cached scores)
│   │   │   ├── recommendation.py          # Cached / generated recommendations
│   │   │   ├── history.py                 # SearchHistory table
│   │   │   └── criteria.py                # ScoringCriteria table (admin-editable thresholds)
│   │   ├── schemas/                       # Pydantic v2 validation schemas
│   │   │   ├── user.py                    # User creation, login, response DTOs
│   │   │   ├── product.py                 # Product DTOs and nutritional facts
│   │   │   ├── score.py                   # Multi-tier score envelopes & explanations
│   │   │   ├── recommendation.py          # Recommendation payload with delta improvements
│   │   │   └── criteria.py                # Scoring criteria update schemas
│   │   ├── services/                      # Business Logic & Orchestration
│   │   │   ├── product_service.py         # Product entity management
│   │   │   ├── search_service.py          # 3-tier search (DB -> OFF API -> DB Cache)
│   │   │   ├── analysis_service.py        # Coordinate scientific, rule & ML computations
│   │   │   ├── recommendation_service.py  # Multi-criteria alternative ranking
│   │   │   └── off_client.py              # Resilient HTTP client for Open Food Facts
│   │   ├── scoring/                       # Analytical & Scientific Scoring Core
│   │   │   ├── scientific/
│   │   │   │   ├── nutri_score_2023.py    # Official 2023 updated Nutri-Score calculation
│   │   │   │   ├── normalizer.py          # Continuous 0-100 sub-score mathematical curves
│   │   │   │   └── renormalizer.py        # Null-safe dynamic weight renormalizer
│   │   │   └── rules/
│   │   │       ├── additive_evaluator.py  # Informational flags and additive rules
│   │   │       ├── ingredient_quality.py  # Sugar rank position & whole grain detection
│   │   │       └── nova_evaluator.py      # NOVA processing level interpretation
│   │   ├── ml/                            # Machine Learning Inference Wrapper (Fast inference only)
│   │   │   ├── model_loader.py            # Singleton artifact loader for joblib models
│   │   │   ├── category_classifier.py     # Supervised product text category prediction
│   │   │   ├── nutrient_predictor.py      # Nutritional profile validation model
│   │   │   └── similarity_engine.py       # Hybrid TF-IDF + Nutrient KNN similarity calculator
│   │   └── utils/                         # Helper utilities
│   │       ├── barcode_validator.py       # GTIN / EAN check digit validation
│   │       └── text_cleaner.py            # Ingredient string tokenizer and normalizer
│   ├── tests/                             # Automated test suite
│   │   ├── conftest.py                    # Pytest fixtures and mock DB sessions
│   │   ├── test_scoring.py                # Tests for Nutri-Score 2023, solid vs beverage
│   │   ├── test_renormalization.py        # Missing nutrient handling tests
│   │   ├── test_barcode.py                # Barcode validation unit tests
│   │   ├── test_recommendations.py        # Recommendation logic and differential tests
│   │   └── test_api.py                    # FastAPI test client integration endpoints
│   ├── alembic/                           # Database migration scripts
│   ├── seed_data.py                       # Offline demonstration database seeder
│   └── requirements.txt                   # Backend dependencies
├── ml/                                    # Machine Learning Training & Research Pipeline
│   ├── data/                              # Raw and processed training datasets
│   │   ├── raw/                           # Filtered Open Food Facts JSONL / CSV exports
│   │   └── processed/                     # Train/test split matrices
│   ├── notebooks/                         # Exploratory data analysis (EDA) notebooks
│   │   ├── 01_eda_and_cleaning.ipynb
│   │   └── 02_model_experimentation.ipynb
│   ├── training/                          # Offline training scripts
│   │   ├── train_category_classifier.py   # Trains TF-IDF + Logistic Regression / SVM
│   │   └── train_nutrient_classifier.py   # Trains Random Forest nutrient classifier
│   ├── evaluation/                        # Model validation reports & confusion matrices
│   │   └── evaluate_models.py             # Computes Macro F1, Precision, Recall, Curves
│   └── artifacts/                         # Serialized trained model files (.joblib)
├── frontend/                              # Modern React Client Application
│   ├── public/                            # Favicon, assets
│   ├── src/
│   │   ├── api/                           # Axios instance and API call wrappers
│   │   ├── components/                    # Reusable UI component library
│   │   │   ├── common/                    # Navbar, Footer, Modal, Badges, Alert
│   │   │   ├── search/                    # SearchBar, BarcodeScannerModal, FilterBar
│   │   │   ├── product/                   # ProductCard, NutritionTable, IngredientList
│   │   │   ├── scoring/                   # NutriScoreBadge, ScoreGauge, ParameterBarChart
│   │   │   ├── comparison/                # ComparisonMatrix, RadarComparison
│   │   │   └── admin/                     # CriteriaEditorTable, AuditLogs
│   │   ├── context/                       # AuthContext, NotificationContext
│   │   ├── hooks/                         # useProduct, useSearch, useAuth
│   │   ├── pages/                         # Main application views (9 distinct pages)
│   │   ├── types/                         # TypeScript interfaces (matching Pydantic schemas)
│   │   ├── utils/                         # Formatter, color helpers, error parsers
│   │   ├── App.tsx                        # Router layout and route definitions
│   │   └── main.tsx                       # React DOM entry point
│   ├── tailwind.config.js                 # Tailwind styling rules
│   ├── vite.config.ts                     # Vite build configuration
│   └── package.json                       # Frontend dependencies
├── docker-compose.yml                     # Docker configuration for PostgreSQL
└── README.md                              # Main project documentation & run instructions
```

---

## 2. Detailed Module Responsibilities

### 2.1 Backend Route Handlers (`app/api/`)
- **Responsibility**: Receive HTTP requests, deserialize JSON using Pydantic, validate authorization via JWT header dependencies, call relevant Services, and serialize response models.
- **Contract**: Zero business or calculation logic. Any data modification, scoring calculation, or external lookup is delegated to `app/services/`.

### 2.2 Backend Service Layer (`app/services/`)
- **Responsibility**: Orchestrates domain workflows.
  - `search_service.py`: Enforces the 3-tier lookup pattern (Local DB -> Open Food Facts -> Local Cache).
  - `analysis_service.py`: Queries product nutrition, calls `app/scoring/scientific/` for baseline mathematical scores, calls `app/scoring/rules/` for heuristic flags, and queries `app/ml/` for category or profile validation.
  - `recommendation_service.py`: Identifies peer products in the same category, executes the hybrid ML similarity + nutrient KNN filter, and formats per-parameter improvement explanations.
  - `off_client.py`: Uses `httpx` with timeout management and exponential backoff retry to query Open Food Facts API v2.

### 2.3 Scientific Scoring Engine (`app/scoring/scientific/`)
- **Responsibility**: Pure, deterministic mathematical evaluations based on scientific standards.
  - `nutri_score_2023.py`: Strict implementation of the Santé Publique France 2023 revised Nutri-Score calculation (differentiating general solid food vs beverages per 100ml, accounting for negative points [energy, sugar, sat fat, sodium] and positive points [protein, fiber, fruits/vegetables]).
  - `normalizer.py`: Transforms real nutrient values into continuous 0–100 sub-scores using calibrated non-linear sigmoid or linear piecewise functions.
  - `renormalizer.py`: If a nutrient (e.g., fiber or saturated fat) is `None`, omits its weight and scales the remaining available criteria weights so the total weight sums to 1.0 (100%), producing a `confidence_score` (e.g., 0.83).

### 2.4 Rule-Based Scoring Engine (`app/scoring/rules/`)
- **Responsibility**: Heuristic, transparent logic clearly demarcated from scientific standards.
  - `additive_evaluator.py`: Matches detected E-numbers/INS against an evidence dictionary to produce neutral warnings (e.g., "Contains Artificial Sweetener E951 Aspartame").
  - `ingredient_quality.py`: Evaluates whether sugars/refined syrups appear in the top 3 ingredients and counts total processing markers.

### 2.5 Machine Learning Engine (`app/ml/` & `/ml`)
- **Separation**:
  - `/ml/`: Standalone offline environment for data cleaning, exploratory analysis, hyperparameter tuning, and model evaluation metrics generation.
  - `backend/app/ml/`: Minimalist, zero-training inference wrapper that loads pre-trained `.joblib` pipelines at FastAPI startup and provides thread-safe inference methods.
- **ML Responsibilities**:
  1. *Food Category Classifier*: Predicts standard product category from product title and ingredient text.
  2. *Alternative Product Similarity*: High-dimensional text TF-IDF combined with standard-scaled nutrient KNN to find close nutritional peer products.
