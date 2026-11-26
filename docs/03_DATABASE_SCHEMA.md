# 03. Database Schema Specification

## 1. Relational Entity-Relationship (ER) Diagram

The Smart Shopping Assistant employs a fully normalized relational database design (PostgreSQL with SQLite fallback). Nutritional information, ingredients, criteria thresholds, and scores are decomposed into distinct, indexed relational tables—strictly avoiding unindexed JSON blobs.

```mermaid
erDiagram
    USERS ||--o{ SEARCH_HISTORY : records
    USERS ||--o{ RECOMMENDATIONS : receives
    CATEGORIES ||--o{ PRODUCTS : categorizes
    CATEGORIES ||--o{ SCORING_CRITERIA : defines_thresholds
    PRODUCTS ||--|| NUTRITIONAL_INFORMATION : possesses
    PRODUCTS ||--o{ PRODUCT_INGREDIENTS : contains
    INGREDIENTS ||--o{ PRODUCT_INGREDIENTS : used_in
    PRODUCTS ||--o{ PRODUCT_SCORES : evaluated_as
    PRODUCTS ||--o{ RECOMMENDATIONS : target_product
    PRODUCTS ||--o{ RECOMMENDATIONS : recommended_alternative
    PRODUCTS ||--o{ SEARCH_HISTORY : queried_product

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string role "user | admin"
        datetime created_at
        datetime updated_at
    }

    CATEGORIES {
        integer id PK
        string name UK
        string slug UK
        string product_type "solid | beverage"
        string description
        integer parent_id FK "nullable"
        datetime created_at
    }

    PRODUCTS {
        uuid id PK
        string barcode UK "GTIN-8/12/13/14"
        string name
        string brand
        string generic_name
        integer category_id FK
        string serving_size "e.g. 100g, 250ml"
        string image_url
        string packaging
        string origin_country
        integer nova_group "1, 2, 3, 4 nullable"
        string nutri_score_grade "A, B, C, D, E nullable"
        float data_completeness_score "0.0 - 1.0"
        string data_source "local_seed | open_food_facts"
        datetime created_at
        datetime updated_at
    }

    NUTRITIONAL_INFORMATION {
        uuid id PK
        uuid product_id FK UK
        float energy_kcal "nullable"
        float energy_kj "nullable"
        float fat_g "nullable"
        float saturated_fat_g "nullable"
        float trans_fat_g "nullable"
        float carbohydrates_g "nullable"
        float sugars_g "nullable"
        float added_sugars_g "nullable"
        float fiber_g "nullable"
        float proteins_g "nullable"
        float sodium_mg "nullable"
        float salt_g "nullable"
        float fruits_vegetables_nuts_colza_walnut_olive_oils_pct "nullable (for Nutri-Score)"
        string basis "per 100g | per 100ml"
        datetime updated_at
    }

    INGREDIENTS {
        uuid id PK
        string canonical_name UK
        string ins_number "E-number / INS code nullable"
        boolean is_additive
        string additive_type "sweetener | preservative | color | flavor | emulsifier"
        string health_note "Neutral objective description"
        datetime created_at
    }

    PRODUCT_INGREDIENTS {
        uuid id PK
        uuid product_id FK
        uuid ingredient_id FK
        integer position_order "1-indexed order on label"
        float estimated_percentage "nullable"
        boolean is_whole_grain
        boolean is_allergen
    }

    SCORING_CRITERIA {
        integer id PK
        integer category_id FK
        string product_type "solid | beverage"
        string parameter_name "sugar | sodium | saturated_fat | energy | protein | fiber | ingredient_quality"
        float weight "Decimal weight summing to 1.0"
        float low_threshold "WHO/FSSAI Green Cut-off"
        float medium_threshold "WHO/FSSAI Amber Cut-off"
        float high_threshold "WHO/FSSAI Red Cut-off"
        string unit "g | mg | kcal"
        string polarity "negative (lower is better) | positive (higher is better)"
        datetime updated_at
    }

    PRODUCT_SCORES {
        uuid id PK
        uuid product_id FK
        float overall_project_score "0 - 100 continuous"
        string project_health_band "Healthy | Moderate | Unhealthy"
        string official_nutri_score_grade "A | B | C | D | E"
        integer official_nutri_score_points "Integer points"
        float confidence_score "0.0 - 1.0 based on available data"
        string sub_scores_json "Per-parameter 0-100 values & status"
        string pros_json "Human-readable positive observations"
        string cons_json "Human-readable negative warnings"
        string scoring_engine_version "e.g. 1.0.0"
        datetime calculated_at
    }

    RECOMMENDATIONS {
        uuid id PK
        uuid target_product_id FK
        uuid alternative_product_id FK
        float similarity_score "Cosine + KNN combined similarity (0-1)"
        float score_improvement "Delta project score"
        string parameter_deltas_json "e.g. {sugar: -45%, fiber: +120%}"
        string explanation "Human-readable reason why superior"
        datetime generated_at
    }

    SEARCH_HISTORY {
        uuid id PK
        uuid user_id FK "nullable for anonymous"
        uuid product_id FK "nullable if search had no match"
        string query_term
        string query_type "barcode | text | category"
        datetime searched_at
    }
```

---

## 2. Table Definitions & Data Dictionary

### 2.1 Table: `users`
Stores user identities, administrative privileges, and authorization secrets.
- `id` (UUID, Primary Key, Indexed)
- `email` (VARCHAR(255), Unique, Not Null, Indexed)
- `hashed_password` (VARCHAR(255), Not Null)
- `full_name` (VARCHAR(255), Not Null)
- `role` (VARCHAR(50), Not Null, Default: `'user'`) — `'admin'` or `'user'`
- `created_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)
- `updated_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.2 Table: `categories`
Hierarchical taxonomy distinguishing between solid foods and beverages.
- `id` (INTEGER, Primary Key, Auto-increment)
- `name` (VARCHAR(100), Unique, Not Null)
- `slug` (VARCHAR(100), Unique, Not Null, Indexed)
- `product_type` (VARCHAR(20), Not Null) — `'solid'` or `'beverage'` (Determines scoring threshold curves)
- `description` (TEXT, Nullable)
- `parent_id` (INTEGER, Foreign Key referencing `categories.id`, Nullable)
- `created_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.3 Table: `products`
Core product catalog entities with provenance and data completeness tracking.
- `id` (UUID, Primary Key, Indexed)
- `barcode` (VARCHAR(32), Unique, Not Null, Indexed) — Validated GTIN-8, UPC-12, EAN-13, ITF-14
- `name` (VARCHAR(255), Not Null, Indexed)
- `brand` (VARCHAR(255), Nullable, Indexed)
- `generic_name` (VARCHAR(255), Nullable)
- `category_id` (INTEGER, Foreign Key referencing `categories.id`, Not Null, Indexed)
- `serving_size` (VARCHAR(100), Nullable)
- `image_url` (VARCHAR(1024), Nullable)
- `packaging` (VARCHAR(100), Nullable)
- `origin_country` (VARCHAR(100), Nullable)
- `nova_group` (SMALLINT, Nullable) — 1 (Unprocessed), 2 (Processed culinary), 3 (Processed), 4 (Ultra-processed)
- `nutri_score_grade` (VARCHAR(2), Nullable) — Official letter grade ('A', 'B', 'C', 'D', 'E')
- `data_completeness_score` (FLOAT, Not Null, Default: 0.0) — Calculated fraction ($0.0 - 1.0$) of mandatory nutritional values present
- `data_source` (VARCHAR(50), Not Null, Default: `'local_seed'`) — `'local_seed'` or `'open_food_facts'`
- `created_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)
- `updated_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.4 Table: `nutritional_information`
Normalized nutritional facts strictly standardized per 100g (for solids) or per 100ml (for beverages).
- **Rule**: Missing nutrient fields are strictly stored as `NULL` (`None`), never substituted with `0.0`.
- `id` (UUID, Primary Key)
- `product_id` (UUID, Foreign Key referencing `products.id`, Unique, Not Null, Indexed)
- `energy_kcal` (FLOAT, Nullable) — Energy in kcal per 100g/ml
- `energy_kj` (FLOAT, Nullable) — Energy in kJ per 100g/ml
- `fat_g` (FLOAT, Nullable) — Total fat in grams
- `saturated_fat_g` (FLOAT, Nullable) — Saturated fatty acids in grams
- `trans_fat_g` (FLOAT, Nullable) — Trans fats in grams
- `carbohydrates_g` (FLOAT, Nullable) — Total carbohydrates in grams
- `sugars_g` (FLOAT, Nullable) — Total sugars in grams
- `added_sugars_g` (FLOAT, Nullable) — Added sugars in grams
- `fiber_g` (FLOAT, Nullable) — Dietary fiber in grams
- `proteins_g` (FLOAT, Nullable) — Proteins in grams
- `sodium_mg` (FLOAT, Nullable) — Sodium in milligrams (derived from salt or directly recorded)
- `salt_g` (FLOAT, Nullable) — Salt in grams ($1\text{g salt} \approx 400\text{mg sodium}$)
- `fruits_vegetables_nuts_colza_walnut_olive_oils_pct` (FLOAT, Nullable) — Percentage component (0-100%) for Nutri-Score positive point calculations
- `basis` (VARCHAR(20), Not Null, Default: `'per 100g'`) — `'per 100g'` or `'per 100ml'`
- `updated_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.5 Table: `ingredients`
Canonical ingredient registry with additive classification and objective descriptions.
- `id` (UUID, Primary Key, Indexed)
- `canonical_name` (VARCHAR(255), Unique, Not Null, Indexed)
- `ins_number` (VARCHAR(20), Nullable, Indexed) — e.g. `'E950'`, `'INS 330'`
- `is_additive` (BOOLEAN, Not Null, Default: `FALSE`)
- `additive_type` (VARCHAR(50), Nullable) — `'sweetener'`, `'preservative'`, `'color'`, etc.
- `health_note` (TEXT, Nullable) — Neutral scientific descriptor
- `created_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.6 Table: `product_ingredients`
Many-to-many relationship preserving the exact declaration order from the food label.
- `id` (UUID, Primary Key)
- `product_id` (UUID, Foreign Key referencing `products.id`, Not Null, Indexed)
- `ingredient_id` (UUID, Foreign Key referencing `ingredients.id`, Not Null, Indexed)
- `position_order` (INTEGER, Not Null) — 1-indexed order (1 = primary ingredient by weight)
- `estimated_percentage` (FLOAT, Nullable) — Specified if disclosed on packaging
- `is_whole_grain` (BOOLEAN, Not Null, Default: `FALSE`)
- `is_allergen` (BOOLEAN, Not Null, Default: `FALSE`)

### 2.7 Table: `scoring_criteria`
Dynamic, administrative configuration of parameter weights and health cut-offs.
- **Rule**: Eliminates hardcoded magic numbers from the codebase. Allows administrators to fine-tune weights for solid foods vs beverages.
- `id` (INTEGER, Primary Key, Auto-increment)
- `category_id` (INTEGER, Foreign Key referencing `categories.id`, Nullable) — If null, serves as global default for `product_type`
- `product_type` (VARCHAR(20), Not Null) — `'solid'` or `'beverage'`
- `parameter_name` (VARCHAR(50), Not Null) — `'sugar'`, `'sodium'`, `'saturated_fat'`, `'energy'`, `'protein'`, `'fiber'`, `'ingredient_quality'`
- `weight` (FLOAT, Not Null) — Fractional weight (e.g. 0.20 for sugar)
- `low_threshold` (FLOAT, Not Null) — Green traffic light upper limit (FSSAI/WHO)
- `medium_threshold` (FLOAT, Not Null) — Amber traffic light upper limit
- `high_threshold` (FLOAT, Not Null) — Red traffic light lower limit
- `unit` (VARCHAR(20), Not Null) — `'g'`, `'mg'`, `'kcal'`
- `polarity` (VARCHAR(20), Not Null) — `'negative'` (lower is healthier) or `'positive'` (higher is healthier)
- `updated_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.8 Table: `product_scores`
Cached, explainable evaluation records.
- `id` (UUID, Primary Key, Indexed)
- `product_id` (UUID, Foreign Key referencing `products.id`, Not Null, Indexed)
- `overall_project_score` (FLOAT, Not Null) — 0.0 to 100.0 continuous score
- `project_health_band` (VARCHAR(30), Not Null) — `'Healthy'` (>= 70), `'Moderate'` (40-69), `'Unhealthy'` (< 40)
- `official_nutri_score_grade` (VARCHAR(2), Not Null) — `'A'`, `'B'`, `'C'`, `'D'`, `'E'`
- `official_nutri_score_points` (INTEGER, Not Null) — Nutri-Score 2023 integer score
- `confidence_score` (FLOAT, Not Null) — Completeness ratio of evaluated parameters ($0.0 - 1.0$)
- `sub_scores_json` (TEXT, Not Null) — JSON-encoded dict of per-parameter sub-scores and status
- `pros_json` (TEXT, Not Null) — JSON array of data-derived positive statements
- `cons_json` (TEXT, Not Null) — JSON array of data-derived nutritional flags
- `scoring_engine_version` (VARCHAR(20), Not Null, Default: `'1.0.0'`)
- `calculated_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.9 Table: `recommendations`
Stores generated alternative recommendations with pairwise improvement metrics.
- `id` (UUID, Primary Key, Indexed)
- `target_product_id` (UUID, Foreign Key referencing `products.id`, Not Null, Indexed)
- `alternative_product_id` (UUID, Foreign Key referencing `products.id`, Not Null, Indexed)
- `similarity_score` (FLOAT, Not Null) — Multi-factor similarity score ($0.0 - 1.0$)
- `score_improvement` (FLOAT, Not Null) — Delta project score ($\Delta = \text{Score}_{\text{alt}} - \text{Score}_{\text{target}}$)
- `parameter_deltas_json` (TEXT, Not Null) — Granular delta percentages (e.g. `{"sugar": -52.0, "sodium": -30.5}`)
- `explanation` (TEXT, Not Null) — Text explaining why the alternative is superior
- `generated_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.10 Table: `search_history`
Audits search queries and user trends.
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key referencing `users.id`, Nullable, Indexed)
- `product_id` (UUID, Foreign Key referencing `products.id`, Nullable, Indexed)
- `query_term` (VARCHAR(255), Not Null)
- `query_type` (VARCHAR(50), Not Null) — `'barcode'`, `'text'`, `'category'`
- `searched_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.11 Table: `saved_products`
User bookmarks and personalized product monitoring.
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key referencing `users.id`, Not Null, Indexed)
- `product_id` (UUID, Foreign Key referencing `products.id`, Not Null, Indexed)
- `notes` (TEXT, Nullable)
- `created_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.12 Table: `admin_audit_logs`
Immutable security and operational audit trail of administrative modifications.
- `id` (UUID, Primary Key)
- `admin_user_id` (UUID, Foreign Key referencing `users.id`, Not Null, Indexed)
- `action` (VARCHAR(50), Not Null) — `'CREATE'`, `'UPDATE'`, `'DELETE'`, `'CRITERIA_UPDATE'`
- `target_entity` (VARCHAR(50), Not Null) — `'product'`, `'category'`, `'scoring_criteria'`
- `target_id` (VARCHAR(100), Not Null)
- `changes_json` (TEXT, Not Null) — Structured before/after delta JSON
- `created_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)

### 2.13 Table: `scoring_version_history`
Chronological versioning registry for scoring criteria and catalog re-scoring states.
- `id` (INTEGER, Primary Key, Auto-increment)
- `version` (VARCHAR(20), Not Null, Unique) — e.g. `'1.0.0'`, `'1.1.0'`, `'1.2.0'`
- `released_at` (TIMESTAMP WITH TIME ZONE, Default: `NOW()`)
- `description` (TEXT, Not Null)
- `is_active` (BOOLEAN, Not Null, Default: `TRUE`)

