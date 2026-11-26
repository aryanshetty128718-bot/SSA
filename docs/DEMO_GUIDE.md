# Smart Shopping Assistant (SSA) - Local Demonstration Guide

**Target Environment:** Local Windows Machine (Offline Demo-Ready for Academic MCA Viva)  
**Default Database:** SQLite (`smart_shopping.db` — zero configuration required)  
**Frontend URL:** `http://localhost:5173`  
**Backend URL:** `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)  
**Scoring Engine Version:** `v1.2.0` (Project-defined continuous scoring with natural sugar exemption and sub-brand preserving duplicate filter)

---

## 1. Quick Local Start Commands

Run these from PowerShell in the project root:
```powershell
# 1. Setup (run once)
.\setup.ps1

# 2. Start Backend (Terminal 1)
.\run_backend.ps1

# 3. Start Frontend (Terminal 2)
.\run_frontend.ps1

# 4. Automated Tests
.\run_tests.ps1
```

---

## 2. Tested Demonstration Barcode Matrix

> [!NOTE]
> Synthetic products seeded by `seed_data.py` are explicitly marked as **SAMPLE DATA (synthetic, for testing)** and carry a visual "Sample Data" badge in the UI. Real products imported from Open Food Facts are marked with their genuine verified OFF metadata.

| # | Test Scenario | Barcode | Product Name & Brand | Data Source | Expected Project Score & Band | Expected Nutri-Score 2023 | Key Academic Demonstration |
|---|---|---|---|---|---|---|---|
| **1** | **High-Sugar Product (Sugar Cap Rule)** | `3017620422003` | **Nutella** (Ferrero) | **Real OFF Record** | **37.0 / 100** (Red Band, Low) | **Grade E** | Severe sugar (56.3g/100g) activates the configured Sugar Cap rule ($\le 39.0$). Returns 4 healthier peanut/nut butter alternatives. |
| **2** | **Real Indian Biscuit Product** | `8901063023901` | **Marie Gold** (Britannia) | **Real OFF Record** (GS1 India 890) | **50.6 / 100** (Amber Band, Medium) | **Not Computable** | Real Indian market biscuit; demonstrates category coherence and sub-brand preserving near-duplicate filter (other Britannia biscuit lines are permitted; identical Marie Gold pack sizes are excluded). |
| **3** | **Real Beverage (Liquid Scoring Rules)** | `5449000000439` | **Coca Cola Original Taste 1.5L** (Coca-Cola) | **Real OFF Record** | **32.8 / 100** (Red Band, Low) | **Grade E** | Evaluated under liquid rules: 40% sugar weight, stricter cut-offs (1.0g low / 5.0g high). High-sugar beverage warning generated. |
| **4** | **Low-Data Real Product (Missing Nutrients)** | `0012700158042` | **Skinner Spaghetti** (New World Pasta Company) | **Real OFF Record** | **55.0 / 100** (Amber Band, Medium) | **Not Computable** (Reference Standard) | Missing sugars, saturated fat, and sodium in official declaration. Data confidence displays **42%** with explicit missing field breakdown. Nutri-Score displays "Not Computable" without arbitrary 0.0 imputation. |
| **5** | **Synthetic Healthy Benchmark** | `8901058800012` | **Traditional Rolled Oats** (PureHarvest) | **SAMPLE DATA** (Synthetic, for testing) | **87.7 / 100** (Green Band, High) | **Grade A** | Demonstrates concave positive nutrient rewards (10.6g dietary fiber, 12.0g protein, 0.8g sugar). Renders amber "Sample Data" badge in UI. |
| **6** | **Synthetic Diet Beverage** | `8901058800081` | **Zero Sugar Cola Beverage** (SparkleSip) | **SAMPLE DATA** (Synthetic, for testing) | **68.5 / 100** (Amber Band, Medium) | **Grade B** | Demonstrates beverage hierarchy: Water (100) > Diet Cola (68.5) > Fruit Juice > Regular Cola (32.8). |
| **7** | **Synthetic Indian High-Sodium Snack** | `8901058800258` | **Traditional Deep-Fried Masala Bhujia** | **SAMPLE DATA** (Synthetic, for testing) | **24.5 / 100** (Red Band, Low) | **Grade E** | Synthetic test record demonstrating extreme sodium and saturated fat penalty under NOVA Group 4 ultra-processed profiling. |
| **8** | **Two-Level Hybrid Recommendations (Nutella)** | `3017620422003` | **Nutella Alternatives** (`/alternatives/3017620422003`) | **Real Catalog** | — | — | Recommends 5 healthier culinary alternatives. Same-type hazelnut spreads lack higher scores, triggering Tier 2 related culinary alternatives (Kashi GO, Mcennedy, Andros Be Nuts) with `Related type: Peanut Butter` badges and ingredient similarity chips. Tier 3 unrelated categories are strictly 0.0%. |
| **9** | **Product Comparison (3 Items)** | `/compare?ids=3017620422003,5449000000439,8901063023901` | Nutella vs Coca-Cola vs Marie Gold | **Real Catalog** | — | — | Side-by-side 8-nutrient comparison matrix, Recharts profile visualization, best-performer highlights, and trade-off summary verdict. |
| **10** | **Invalid Check Digit Error Handling** | `4006381333930` | *(Invalid Barcode)* | **Validation Test** | — | — | Expected check digit is 1, but got 0. Triggers instant HTTP 422 Unprocessable Entity error before hitting external services. |
| **11** | **Valid EAN-13 Not In Database (Manual Entry Fallback)** | `8909999999994` | *(Valid Uncached Barcode)* | **Manual Entry Demo** | — | — | Mathematically valid EAN-13 check digit (4). When unindexed upstream, UI offers "Enter Product Manually" with physiological bounds validation (`sugars <= carbs`, `sat fat <= fat`), immediate scoring, and "Entered by a user; not verified" badge. |

---

## 3. Recommended Viva Walkthrough Steps

### Step 1: Scan / Search Nutella (`3017620422003`)
1. On the Home page search bar, enter `3017620422003`.
2. Inspect the analysis result:
   - **Dual Badging:** Proposed Project Score (37.1) vs Official Reference Nutri-Score (Grade E).
   - **Scoring Engine Version:** Displays `Scoring Engine v1.2.0` linked to methodology.
   - **Declared Nutrition Table:** Full 9-row breakdown with red highlights on high sugar (56.3g/100g) and saturated fat (10.6g/100g).
   - **Ingredients Tab:** Ingredients displayed with additive detection.
   - **Sugar Cap Notification:** Score capped because sugar exceeds severe threshold (30.0g).
3. Click **"Find Healthier Alternatives"**:
   - Displays 5 healthier alternatives (Kashi GO Peanut Butter Crunch, Mcennedy, Menguy's, Andros Be Nuts, Nature Valley) with +13.9 to +29.4 score improvements.
   - Shows Tier Badges (`Related type: Peanut Butter`), Ingredient Match chips, and transparent trade-offs (e.g. higher energy or sodium).

### Step 2: Test Low-Data Handling (`0012700158042`)
1. Search barcode `0012700158042` (Skinner Spaghetti by New World Pasta Company, verified real OFF product).
2. Point out:
   - **Nutri-Score Badge:** Displays **"Not Computable"** (gray badge) because mandatory algorithm inputs (sugars, saturated fat, sodium) are not declared in the OFF record.
   - **Data Confidence Meter:** Displays **42% Confidence (Low)** with explicit missing parameters list.
   - **Dynamic Weight Renormalization:** The scoring engine redistributes weights across available parameters rather than substituting zero.

### Step 3: Beverage Physical State & Stricter Cut-offs (`5449000000439`)
1. Search `5449000000439` (Coca Cola Original Taste 1.5L).
2. Point out:
   - Physical type badge: `Beverage (Liquid)`.
   - Stricter cut-offs: 1.0g low / 5.0g high sugar per 100ml.
   - 40% effective weight allocated to sugar for beverages.

### Step 4: Multi-Product Side-by-Side Comparison (`/compare`)
1. Open the Comparison tool (`/compare?ids=3017620422003,5449000000439,8901063023901`).
2. Review the side-by-side comparison across Nutella, Coca-Cola, and Marie Gold:
   - 8-nutrient parameter comparison table with best performers highlighted in green.
   - Recharts visual bar chart.
   - Nuanced summary verdict explaining trade-offs.

### Step 5: Admin Panel, Version Bump & Re-scoring
1. Log in via `/login` with administrator credentials (`admin@example.com` / `Admin@12345`).
2. Navigate to `/admin` -> "Scoring Engine Config":
   - Edit a parameter weight (e.g. adjust sugar weight).
   - Form validates that weights sum to exactly 1.000.
   - Click "Save & Trigger Background Re-scoring": version bumps incrementally in DB and audit log.
   - Progress bar tracks re-scoring status.
