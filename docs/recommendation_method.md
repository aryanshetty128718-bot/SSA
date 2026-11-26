# Hybrid Tiered Recommendation Methodology

## 1. Overview and Problem Statement
In nutritional recommendation systems, proposing alternatives from the broad level-1 category can lead to severe culinary incoherence (e.g., recommending plain yogurt or chewing gum for chocolate cookies, or sparkling water for dark chocolate). While such swaps may mathematically improve a nutrient score, consumers reject them because they do not fulfill the culinary context or consumption occasion.

To solve this, the Smart Shopping Assistant implements a **Two-Level Taxonomy** with a **Tiered Hybrid Recommendation Engine**:
- **Level 1 (Broad Category):** 11 statutory categories (e.g., `breakfast-cereals`, `sweet-spreads-nut-butters`, `instant-noodles-pasta`).
- **Level 2 (Specific Product Type):** 45 granular culinary types (e.g., `oats-porridge`, `muesli-granola`, `pasta`, `instant-noodles`, `peanut-butter`, `hazelnut-chocolate-spread`).

---

## 2. Recommendation Tiering Architecture

| Recommendation Tier | Scope | Candidate Criteria | Eligibility Condition |
| :--- | :--- | :--- | :--- |
| **Tier 1: Same Product Type** | Identical Level-2 culinary type | Same product type (e.g., Rolled Oats $\rightarrow$ Steel Cut Oats, Pasta $\rightarrow$ Whole Wheat Pasta) | Primary candidate pool. Preferred whenever $\ge 5$ qualified candidates exist. |
| **Tier 2: Related Culinary Type** | Documented culinary equivalent | Sibling type within category (e.g., Chocolate Spread $\rightarrow$ Peanut Butter, Oats $\rightarrow$ Granola, Cola $\rightarrow$ Flavoured Soda) | Activated **only if** Tier 1 yields $< 5$ qualified candidates. |
| **Tier 3: Unrelated Type** | Cross-type culinary leap | Divergent types (e.g., Chips $\rightarrow$ Yogurt, Cola $\rightarrow$ Milk) | **Strictly disqualified (0% allowed).** |

---

## 3. Mathematical Ranking Formulation

Candidates surviving quality gates (data completeness $\ge 80\%$, computable Nutri-Score, trade-off checks) are ranked by the deterministic composite score:

$$\text{RankScore} = w_{\text{type}} \cdot \text{TypeMatch} + w_{\text{ing}} \cdot \text{Sim}_{\text{ing}} + w_{\text{nut}} \cdot \text{Sim}_{\text{nut}} + w_{\text{gain}} \cdot \Delta\text{Score}_{\text{norm}} - \text{Penalty}_{\text{trade-off}}$$

### Parameter Definitions and Weight Rationale:
1. **$w_{\text{type}} = 0.35$ (Culinary Type Match Weight):**
   - $\text{TypeMatch} = 1.0$ for Tier 1 (Same Product Type).
   - $\text{TypeMatch} = 0.5$ for Tier 2 (Related Culinary Alternative).
   - *Rationale:* Ensures identical food substitutes are prioritized over cross-type swaps.

2. **$w_{\text{ing}} = 0.25$ (Ingredient Formulation Similarity):**
   - Computed as Jaccard similarity on canonical statutory ingredient sets $A$ and $B$:
     $$\text{Sim}_{\text{ing}} = \frac{|A \cap B|}{|A \cup B|}$$
   - *Rationale:* Preserves recipe coherence (e.g., oat bases for muesli, durum wheat for pasta). If ingredient declarations are missing, falls back to text TF-IDF similarity.

3. **$w_{\text{nut}} = 0.15$ (Nutritional Profile Alignment):**
   - Computed as Cosine similarity between standardized nutrient vectors (energy, fat, saturated fat, carbohydrates, sugars, fiber, proteins, sodium):
     $$\text{Sim}_{\text{nut}} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
   - *Rationale:* Guarantees macro-nutrient balance and prevents substituting a high-protein spread with a pure sugar jelly.

4. **$w_{\text{gain}} = 0.25$ (Healthiness Gain):**
   - Normalized score delta:
     $$\Delta\text{Score}_{\text{norm}} = \min\left(1.0, \max\left(0.0, \frac{\text{Score}_{\text{cand}} - \text{Score}_{\text{orig}}}{50.0}\right)\right)$$
   - *Rationale:* Strongly rewards items delivering meaningful nutritional improvements.

5. **$\text{Penalty}_{\text{trade-off}} = 0.10$:**
   - Applied if any trade-off flags exist (e.g., lower sugar but higher sodium).

---

## 4. Trade-Off and Quality Guards
- **Completeness Guard:** Rejects candidates with data completeness $< 80\%$.
- **Nutri-Score Computability:** Only official validated grades A, B, C, D, E are accepted.
- **Trade-off Disqualification:** Disqualifies any candidate where:
  - Sugars increase by $> 5.0\,\text{g}/100\,\text{g}$.
  - Saturated fat increases by $> 3.0\,\text{g}/100\,\text{g}$ into unhealthy territory ($> 5.0\,\text{g}$).
  - Sodium increases by $> 350\,\text{mg}/100\,\text{g}$ into high sodium territory ($> 500\,\text{mg}$).
