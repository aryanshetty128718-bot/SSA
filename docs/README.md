# Smart Shopping Assistant (SSA) - Documentation Index

This directory contains the complete technical specifications, architectural designs, scientific methodology, and machine learning formulation for the **Smart Shopping Assistant** MCA Major Project.

---

## Documentation Index

1. [01. System Architecture](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/01_SYSTEM_ARCHITECTURE.md)
   - High-level multi-tier architecture diagram (Mermaid)
   - Presentation, API, Service, and Persistence layer boundaries
   - Ingress workflow, search sequencing, and security model

2. [02. Module-Wise Breakdown](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/02_MODULE_WISE_BREAKDOWN.md)
   - Monorepo folder layout (`frontend/`, `backend/`, `ml/`, `docs/`)
   - Detailed package responsibilities and interface contracts
   - Strict separation of concerns between API routes, business services, scoring modules, and ML

3. [03. Database Schema Specification](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/03_DATABASE_SCHEMA.md)
   - Complete Entity-Relationship (ER) diagram (Mermaid)
   - 10 normalized relational tables (`users`, `categories`, `products`, `nutritional_information`, `ingredients`, `product_ingredients`, `scoring_criteria`, `product_scores`, `recommendations`, `search_history`)
   - Detailed data dictionary, keys, indexes, and null-safety definitions

4. [04. Machine Learning Implementation Strategy](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/04_ML_IMPLEMENTATION_STRATEGY.md)
   - Dataset acquisition from Open Food Facts (India and Global packaged foods)
   - Model 1: Supervised Food Category Classifier (TF-IDF + Logistic Regression / Linear SVM vs. Random Forest)
   - Model 2: Hybrid Content Similarity & Recommendation Ranking (TF-IDF Cosine + Scaled Nutrient-Vector KNN)
   - Model 3: Nutri-Score Grade Prediction with Tree Feature Importances
   - Model evaluation benchmarks (Accuracy, Macro-F1, Confusion Matrix, 5-Fold Stratified Cross-Validation)
   - Offline training vs. online FastAPI runtime inference with `.joblib` serialization

5. [05. Nutritional Scoring Methodology](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/05_NUTRITIONAL_SCORING_METHODOLOGY.md)
   - Official Nutri-Score 2023 algorithm implementation (Solid food vs. Beverage rules)
   - Proposed Project Continuous 0–100 Scoring Framework
   - Calibrated mathematical curves for negative (sugar, sodium, saturated fat, energy) and positive (protein, fiber) nutrients
   - Dynamic weight renormalization for missing nutritional data (`None` handling)
   - Ingredient quality assessment, sugar ranking position checks, and objective additive rules
   - Beverage (per 100 ml) vs. Solid food (per 100 g) threshold tables

6. [06. API Integration Strategy & REST Endpoints](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/06_API_INTEGRATION_STRATEGY.md)
   - Strict barcode validation (GTIN-8, UPC-12, EAN-13, ITF-14) with Modulo-10 check-digit validation
   - Three-tier search execution: Local Database $\to$ Open Food Facts API v2 $\to$ Cache in Local Database
   - Upstream timeout and malformed payload handling
   - Comprehensive REST endpoint definitions across auth, search, products, analysis, recommendations, and admin

7. [07. Frontend Page & Component Structure](file:///c:/Users/Admin/.gemini/antigravity/scratch/SSA/docs/07_FRONTEND_ARCHITECTURE.md)
   - React 18 + Vite + Tailwind CSS + Recharts + React Router architecture
   - Page breakdown across 9 core application routes
   - Reusable component hierarchy and visual separation of scientific scores, rule flags, and ML insights
   - State management, comparison drawer, and webcam barcode scanner modal
