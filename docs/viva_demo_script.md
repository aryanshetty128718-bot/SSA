# Project Viva Demonstration Script: Smart Shopping Assistant (SSA)

**Project Title:** AI-Based Food and Beverage Analysis and Healthier-Alternative Recommendation Web App  
**Degree:** Master of Computer Applications (MCA) — Major Project  
**Author / Presenter:** MCA Final Year Candidate  
**Live Application URL:** `http://localhost:5173` (Frontend) | `http://localhost:8000/docs` (Backend REST API)  

---

## 1. Demonstration Protocol Overview

This script is structured for a 12–15 minute live examination viva before the Board of Examiners. It provides **8 exact product barcodes** with anticipated numerical scores, badges, and alternative recommendations demonstrating every architectural requirement of the project.

---

## 2. Live Barcode Test Matrix

| # | Product Name | Barcode | Physical Type | Key Scientific Test Case | Anticipated Project Score & Band | Official Nutri-Score 2023 | Healthier Alternatives Expected |
|---|---|---|---|---|---|---|---|
| **1** | **Nutella Hazelnut Spread** (Ferrero, 400g) | `3017620422003` | Solid Food | **Sugar Cap & Category Coherence**: Severe sugar (56.3g/100g) triggers cap at $\le 39.0$. Verifies that alternative products belong to sweet spreads/nut butters, NOT confectionery/gum. | **23.4 / 100** (Red Band, Low) | **Grade E** (Score: 24) | Peanut Butter (e.g. Pintola), Lower-Sugar Hazelnut Spreads, Almond Butter |
| **2** | **Artisan Fruit Bar** (Low-Data Case) | `8000500310427` | Solid Food | **Missing Data & Epistemological Honesty**: Missing sodium/salt. Dynamic Renormalization scores available nutrients; Nutri-Score returns `not_computable` (never 0.0 substitution). | **62.5 / 100** (Amber Band, Medium) | **Not Computable** (Missing: Sodium/Salt) | High-fiber whole date/fig bars with complete nutritional declarations |
| **3** | **Coca-Cola Original** (330ml Can) | `5449000000996` | Beverage | **Strict Beverage Thresholds**: 10.6g sugar/100ml evaluated under project-defined 40% beverage weight and 1.0g/5.0g thresholds. Beverage con generated. | **28.0 / 100** (Red Band, Low) | **Grade E** (Score: 14) | Sparkling spring water, Unsweetened flavored iced tea, Diet cola |
| **4** | **San Pellegrino Sparkling Water** | `8000500003771` | Beverage | **Liquid Benchmark Standard**: 0g sugar, 0 kcal, zero additives. Nutri-Score 2023 assigns exclusive Grade A to water. | **96.5 / 100** (Green Band, High) | **Grade A** (Exclusive to Water) | N/A (Baseline reference drink) |
| **5** | **Britannia Marie Gold Biscuit** | `8901063012570` | Solid Food | **Indian Product & Near-Duplicate Filter**: 890 GS1 India barcode. Recommends alternative biscuits while filtering out 250g vs 500g Marie Gold pack variants. | **48.2 / 100** (Amber Band, Medium) | **Grade D** | Britannia NutriChoice Digestive, Whole wheat oat cookies |
| **6** | **Kellogg's Chocos Cereal** | `8901499008107` | Solid Food | **Sugar Hierarchy & Cap Boundary**: 28.5g sugar triggers high sugar cap ($\le 48.0$). Flagged con: "Sugar is second listed ingredient". | **42.0 / 100** (Amber Band, Medium) | **Grade D** | Quaker Rolled Oats, Unsweetened Muesli, Multigrain Porridge |
| **7** | **Whole Rolled Oats** | `8901058800012` | Solid Food | **Positive Nutrient Benchmark**: 10.6g dietary fiber, 12.0g protein, 0.8g sugar. Concave positive score bonus. | **91.4 / 100** (Green Band, High) | **Grade A** | Steel-cut oats, High-fiber multigrain muesli |
| **8** | **Haldiram's Bhujia Sev** | `8904004400406` | Solid Food | **Sodium & Saturated Fat Double Penalty**: 680mg sodium, 14.5g saturated fat, NOVA Group 4 ultra-processed. | **29.8 / 100** (Red Band, Low) | **Grade E** | Roasted Makhana (Foxnuts), Baked multigrain chips, Roasted chana |

---

## 3. Step-by-Step Viva Execution Plan

### Step 1: Scientific Assessment & Missing Data Honesty (Barcodes 1 & 2)
1. Navigate to `http://localhost:5173/`.
2. Input barcode `3017620422003` (Nutella).
3. **Point out to Examiner**:
   - The dual badge: "Proposed Project Score: 23.4 (Project-Defined Scoring)" alongside "Official Reference Standard: Nutri-Score E".
   - Under Sub-scores: Severe sugar (56.3g) activates the configured sugar cap.
   - Click "View Healthier Alternatives": note that recommendations consist of peanut butters and low-sugar nut spreads. Chewing gums and candies are strictly filtered out by the Category Coherence Gate.
4. Input barcode `8000500310427` (Artisan Fruit Bar).
5. **Point out to Examiner**:
   - Data Confidence gauge: clearly states missing sodium/salt parameters.
   - Nutri-Score badge displays **"Not Computable"** instead of guessing zeroes, upholding Santé publique France mathematical standards.
   - Project score dynamically renormalizes available weights over remaining nutrients.

### Step 2: Beverage Formulation vs Solid Foods (Barcodes 3 & 4)
1. Input barcode `5449000000996` (Coca-Cola).
2. **Point out to Examiner**:
   - Physical state badge: `Beverage (Liquid)`.
   - Sugar threshold: stricter than UK FSA solid traffic-lights (1.0g low / 5.0g high).
   - Generates explicit "High Sugar Beverage (>5.0g/100ml)" con.
3. Contrast with barcode `8000500003771` (San Pellegrino Water):
   - Scores 96.5, Nutri-Score Grade A. Mention that in the 2023 updated Nutri-Score algorithm, water is the sole beverage permitted to receive Grade A.

### Step 3: Product Comparison & Near-Duplicate Filter (Barcodes 5 & 6)
1. Navigate to `/compare`.
2. Select Britannia Marie Gold (`8901063012570`), Kellogg's Chocos (`8901499008107`), and Rolled Oats (`8901058800012`).
3. Show the multi-product side-by-side radar and parameter comparison table.
4. Explain how the near-duplicate filter preserves distinct product sub-brands (e.g. Good Day vs Marie Gold) while discarding size variants (250g vs 500g).

### Step 4: Administrator Operations, Audit Log, and Live Criteria Rescoring
1. Log in to `/admin` using administrator credentials from `.env`.
2. Navigate to "Scoring Engine Config".
3. Point out:
   - Configurable Sub-Score weights summing to 1.000.
   - Configurable Sugar Cap cut-offs.
   - Scoring Version Changelog table displaying v1.0.0, v1.1.0, and v1.2.0 audit records.
4. Point out the live Background Catalog Re-scoring status banner.
5. Review the immutable audit log table under "Audit Logs" tab displaying timestamps, admin IDs, entity names, and JSON diffs.
