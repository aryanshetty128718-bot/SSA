# 05. Nutritional Scoring Methodology

## 1. Scientific Framework & Epistemological Stance

The **Smart Shopping Assistant (SSA)** implements a dual-layer evaluation framework:
1. **Validated External Standard (Nutri-Score 2023)**: Strict mathematical calculation of the official updated Nutri-Score algorithm (Santé Publique France, 2023), distinguishing solid foods (per 100g) and beverages (per 100ml).
2. **Proposed Project Scoring Framework (0–100 Continuous Score)**: A transparent, multi-parameter index designed specifically for this MCA academic project to provide granular, continuous metrics, dynamic missing-data weight renormalization, and explainable sub-score breakdowns.

> **Academic Disclaimer**: The 0–100 composite score is clearly labeled in the user interface and API as the *"Proposed Project Scoring Framework"* and is not presented as a statutory or government-enforced standard.

---

## 2. Official Nutri-Score 2023 Algorithm (Validated Reference)

The 2023 updated Nutri-Score algorithm computes an integer score based on negative points ($N$) for nutrients to limit and positive points ($P$) for nutrients to encourage.

$$\text{Nutri-Score Points} = N - P$$

### 2.1 Solid Foods (per 100g)
- **Negative Points ($N \in [0, 55]$)**:
  - Energy (kJ): 0 to 10 points ($> 3350 \text{ kJ} \implies 10 \text{ pts}$)
  - Sugars (g): 0 to 15 points (revised 2023 curve: $> 45 \text{ g} \implies 15 \text{ pts}$)
  - Saturated Fatty Acids (g): 0 to 10 points ($> 10 \text{ g} \implies 10 \text{ pts}$)
  - Salt (g): 0 to 20 points ($> 4.0 \text{ g} \implies 20 \text{ pts}$, derived from sodium: $\text{Salt} = \text{Sodium (g)} \times 2.5$)
- **Positive Points ($P \in [0, 17]$)**:
  - Dietary Fiber (g): 0 to 5 points ($> 4.7 \text{ g} \implies 5 \text{ pts}$)
  - Protein (g): 0 to 7 points ($> 17 \text{ g} \implies 7 \text{ pts}$)
  - Fruits, Vegetables, Legumes, Nuts, and specific healthy oils (%): 0 to 5 points ($> 80\% \implies 5 \text{ pts}$)
- **Protein Cap Rule**: If $N \ge 11$ points (and fruit/vegetable percentage $\le 80\%$), protein points are excluded from $P$ to avoid masking high sugar/saturated fat with isolated protein additives.
- **Letter Grade Classification (Solid Foods)**:
  - **A**: Score $\le -1$
  - **B**: Score $0 \text{ to } 2$
  - **C**: Score $3 \text{ to } 10$
  - **D**: Score $11 \text{ to } 18$
  - **E**: Score $\ge 19$

### 2.2 Beverages (per 100ml)
Beverages use distinct thresholds reflecting higher liquid bioavailability and rapid glycemic impact:
- Water is the only beverage categorized as **A**.
- Negative Points ($N$): Energy ($> 270 \text{ kJ} \implies 10 \text{ pts}$), Sugars ($> 10.5 \text{ g} \implies 10 \text{ pts}$), Saturated Fat ($> 2.0 \text{ g} \implies 10 \text{ pts}$), Salt ($> 0.5 \text{ g} \implies 10 \text{ pts}$).
- Positive Points ($P$): Fruits/vegetables ($> 80\% \implies 6 \text{ pts}$), Protein ($> 2.4 \text{ g} \implies 4 \text{ pts}$), Fiber ($> 1.2 \text{ g} \implies 3 \text{ pts}$).
- Artificial Sweeteners: In the 2023 revision, the presence of non-nutritive sweeteners adds **4 penalty points** to beverages, preventing artificially sweetened sodas from achieving misleadingly high grades.
- **Letter Grade Classification (Beverages)**:
  - **A**: Exclusively reserved for pure water
  - **B**: Score $\le 2$
  - **C**: Score $3 \text{ to } 6$
  - **D**: Score $7 \text{ to } 9$
  - **E**: Score $\ge 10$

---

## 3. Proposed Project Scoring Framework (0–100 Continuous)

The proposed project score evaluates eight individual sub-scores, each mapped continuously onto a $0 - 100$ scale:

| Parameter | Unit | Direction / Polarity | Standard Solid Weight ($w_i$) | Standard Beverage Weight ($w_i$) |
|---|---|---|---|---|
| **Sugars** | g per 100g/ml | Negative (lower is better) | 0.22 | 0.30 |
| **Sodium / Salt** | mg per 100g/ml | Negative (lower is better) | 0.18 | 0.10 |
| **Saturated Fat** | g per 100g/ml | Negative (lower is better) | 0.18 | 0.10 |
| **Energy** | kcal per 100g/ml | Negative (lower is better) | 0.12 | 0.15 |
| **Dietary Fiber** | g per 100g/ml | Positive (higher is better) | 0.10 | 0.05 |
| **Protein** | g per 100g/ml | Positive (higher is better) | 0.10 | 0.05 |
| **Ingredient Quality** | Composite score | Positive (higher is better) | 0.05 | 0.10 |
| **Additive Profile** | Penalty deductions | Negative (fewer additives) | 0.05 | 0.15 |

---

## 4. Sub-Score Mathematical Formulations

### 4.1 Negative Parameters (Sugars, Sodium, Saturated Fat, Energy)
For nutrients where lower concentrations are healthier, the sub-score $S_{\text{neg}}(x) \in [0, 100]$ uses calibrated reference thresholds ($T_{\text{low}}, T_{\text{med}}, T_{\text{high}}$) based on WHO, FSSAI, and UK FSA traffic light guidelines:

$$S_{\text{neg}}(x) = \begin{cases} 
100 - 30 \left(\frac{x}{T_{\text{low}}}\right) & \text{if } 0 \le x \le T_{\text{low}} \quad (\text{Scores } 70 - 100 \implies \text{Green}) \\ 
70 - 30 \left(\frac{x - T_{\text{low}}}{T_{\text{high}} - T_{\text{low}}}\right) & \text{if } T_{\text{low}} < x \le T_{\text{high}} \quad (\text{Scores } 40 - 70 \implies \text{Amber}) \\ 
\max\left(0, 40 \cdot \exp\left(-\frac{x - T_{\text{high}}}{T_{\text{high}}}\right)\right) & \text{if } x > T_{\text{high}} \quad (\text{Scores } 0 - 40 \implies \text{Red}) 
\end{cases}$$

#### Solid Foods vs. Beverage Threshold Reference Table:
| Parameter | Unit | Solid: $T_{\text{low}}$ | Solid: $T_{\text{high}}$ | Beverage: $T_{\text{low}}$ | Beverage: $T_{\text{high}}$ | Reference Basis |
|---|---|---|---|---|---|---|
| **Sugars** | g/100g(ml) | 5.0 | 22.5 | 2.5 | 11.25 | UK FSA / WHO Cut-off |
| **Sodium** | mg/100g(ml)| 120 | 600 | 120 | 300 | UK FSA / FSSAI (600mg Na $\approx$ 1.5g Salt) |
| **Saturated Fat**| g/100g(ml) | 1.5 | 5.0 | 0.75 | 2.5 | UK FSA Front-of-Pack |
| **Energy** | kcal/100g(ml)| 150 | 450 | 30 | 100 | General Dietary Guidelines |

### 4.2 Positive Parameters (Protein, Dietary Fiber)
For beneficial nutrients, higher values yield higher sub-scores:

$$S_{\text{pos}}(x) = \min\left(100, 100 \times \left(\frac{x}{T_{\text{target}}}\right)^{0.85}\right)$$

Where $T_{\text{target}}$ is the daily reference intake contribution target per 100g:
- **Fiber**: $T_{\text{target}} = 6.0\text{g}$ for solids ($> 6\text{g}$ is classified by FSSAI as "High Fiber"), $T_{\text{target}} = 2.5\text{g}$ for beverages.
- **Protein**: $T_{\text{target}} = 12.0\text{g}$ for solids ($> 10\text{g}$ is classified as "High Protein"), $T_{\text{target}} = 4.0\text{g}$ for beverages.

### 4.3 Ingredient Quality & Transparency Sub-Score ($S_{\text{ing}}$)
Evaluates ingredient integrity based on three objective criteria:
1. **Sugar Hierarchy Check**: If free sugar (sugar, sucrose, high fructose corn syrup, invert sugar) is the #1 listed ingredient, a 30-point deduction applies. If present at position #2 or #3, a 15-point deduction applies.
2. **Whole Food Indicators**: Presence of identifiable whole grains (e.g., oats, whole wheat, brown rice) or whole fruit/vegetable components adds +20 points.
3. **NOVA Processing Degree (when available)**:
   - NOVA 1 (Unprocessed / minimally processed): $100$ pts
   - NOVA 2 (Processed culinary ingredients): $85$ pts
   - NOVA 3 (Processed foods): $65$ pts
   - NOVA 4 (Ultra-processed foods): $35$ pts

### 4.4 Additive Evaluation Sub-Score ($S_{\text{add}}$)
- **Neutral Informational Approach**: Additives are identified using canonical E-numbers and INS classifications.
- Additives legally approved by FSSAI and EFSA are **not** arbitrarily called "toxic".
- However, widespread non-nutritive ultra-processing markers (artificial colors like Tartrazine E102, artificial sweeteners like Aspartame E951, emulsifiers like Carboxymethylcellulose E466) carry documented, transparent deductions of 5–10 points each (capped at a minimum of 0 points).
- Every deduction includes an exact human-readable explanation (e.g., *"Contains artificial color Tartrazine (INS 102); deduction applied per project additive rules"*).

---

## 5. Null-Safe Weight Renormalization

### 5.1 The Missing Data Problem
Food labels frequently omit certain non-mandatory nutrients (e.g., dietary fiber is often omitted on Indian confectionery packaging). **Replacing missing nutrients with $0.0$ falsely penalizes products for negative nutrients (treating missing sugar as zero sugar) or falsely penalizes positive nutrients (treating omitted fiber as zero fiber).**

### 5.2 Mathematical Renormalization Formulation
Let $\mathcal{P} = \{p_1, p_2, \dots, p_K\}$ be the set of all evaluated parameters with baseline weights $w_i \in (0, 1)$ such that $\sum_{i=1}^K w_i = 1.0$.

For any product $j$, let $\mathcal{M}_j \subseteq \mathcal{P}$ denote the subset of parameters with **verified non-null values**. The total available weight $W_{\text{avail}}(j)$ is:

$$W_{\text{avail}}(j) = \sum_{p_i \in \mathcal{M}_j} w_i$$

If $W_{\text{avail}}(j) < 0.50$ (less than 50% of the parameter weights are present), the product is flagged as `INSUFFICIENT_DATA`, and the composite score is returned as `None` with an advisory flag.

Otherwise, for all valid parameters $p_i \in \mathcal{M}_j$, the renormalized weight $w_i^*$ is computed as:

$$w_i^* = \frac{w_i}{W_{\text{avail}}(j)}$$

By construction, the renormalized weights sum to unity:

$$\sum_{p_i \in \mathcal{M}_j} w_i^* = 1.0$$

The final continuous composite project score is:

$$\text{Overall Score}(j) = \sum_{p_i \in \mathcal{M}_j} w_i^* \cdot S_i(x_{ij})$$

### 5.3 Data Completeness & Confidence Metric
Alongside the score, the API returns a continuous confidence index:

$$\text{Confidence Score} = W_{\text{avail}}(j) \in [0.0, 1.0]$$

---

## 6. Score Interpretation & Health Bands

| Continuous Project Score | Band Classification | Badge Color | Interpretation |
|---|---|---|---|
| **70.0 – 100.0** | **Healthy Choice** | Green | High nutrient density, low added sugar, low sodium, minimal ultra-processing |
| **40.0 – 69.9** | **Moderate / Balanced** | Amber | Balanced nutritional profile, acceptable in moderation |
| **0.0 – 39.9** | **Less Healthy / Limit**| Red | High in critical nutrients to limit (sugar, sodium, saturated fat) |

---

## 7. Storage in `ScoringCriteria` Database Table

All cut-offs ($T_{\text{low}}, T_{\text{high}}, T_{\text{target}}$) and baseline weights ($w_i$) are stored in the database `scoring_criteria` table. Administrators can modify weights via the authenticated Admin API without modifying source code or redeploying the application.
