# 06. API Integration Strategy & REST Endpoint Specification

## 1. External Integration Strategy: Open Food Facts

### 1.1 Barcode Validation & Normalization
Before initiating any network request or database query, the system performs rigorous barcode validation (`app/utils/barcode_validator.py`):
1. **Character Validation**: Rejects any non-numeric characters (regex: `^\d+$`).
2. **Length Validation**: Supports standard GS1 formats:
   - GTIN-8 / EAN-8 (8 digits)
   - UPC-A / GTIN-12 (12 digits)
   - EAN-13 / GTIN-13 (13 digits)
   - ITF-14 / GTIN-14 (14 digits)
3. **Modulo-10 Check Digit Verification**: Validates the final check digit using standard GS1 alternating weights ($3 \times \text{odd} + 1 \times \text{even}$).
4. **Invalid Barcode Response**: Returns immediate `422 Unprocessable Entity` with a descriptive message rather than issuing futile upstream network calls.

### 1.2 Three-Tier Search & Caching Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Client as User / Frontend
    participant API as FastAPI Router (/api/v1/search/barcode/{barcode})
    participant Svc as Search Service
    participant DB as Relational DB (PostgreSQL / SQLite)
    participant OFF as Open Food Facts v2 API

    Client->>API: GET /api/v1/search/barcode/8901058852899
    API->>Svc: get_by_barcode("8901058852899")
    Svc->>Svc: Validate Check-Digit
    Svc->>DB: SELECT * FROM products WHERE barcode = :barcode
    alt Cache Hit (Found in Local DB)
        DB-->>Svc: Product Record + Nutrition + Ingredients
        Svc-->>API: Domain Product Entity
    else Cache Miss (Not Found Locally)
        Svc->>OFF: GET https://world.openfoodfacts.org/api/v2/product/{barcode}.json
        alt Found (status = 1)
            OFF-->>Svc: Raw OFF JSON Document
            Svc->>Svc: Extract & clean nutrients, ingredients, and NOVA
            Svc->>DB: INSERT INTO products, nutritional_information, ingredients
            DB-->>Svc: Persisted Product
            Svc-->>API: Domain Product Entity
        else Not Found on OFF (status = 0)
            OFF-->>Svc: 404 / status: 0 ("product not found")
            Svc-->>API: ProductNotFoundException
            API-->>Client: 404 Not Found {"detail": "Product with barcode 8901058852899 not found in local catalog or Open Food Facts"}
        else Network Timeout / 5xx
            OFF-->>Svc: ReadTimeout / HTTP 502/503
            Svc-->>API: ExternalServiceUnavailableException
            API-->>Client: 503 Service Unavailable {"detail": "Open Food Facts API is temporarily unreachable. Please retry shortly."}
        end
    end
    API-->>Client: 200 OK (Product Details + Scores + Data Completeness)
```

### 1.3 Upstream Resilience & Error Handling
- **Timeouts**: Client configured with 5.0s connect timeout and 8.0s read timeout.
- **Malformed Upstream Payloads**: Open Food Facts frequently has nested inconsistencies (e.g., nutrients declared as strings, negative sodium values). The service cleanses input using strict Pydantic v2 parsing rules. Missing nutrient values are mapped explicitly to `None` (never default `0`).

---

## 2. REST API Endpoint Specifications

All endpoints are prefixed with `/api/v1` and return standard JSON with RFC-7807 problem details on error.

### 2.1 Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required | Request Body / Params | Success Status |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user account | None | `UserCreateSchema` (email, password, full_name) | `201 Created` |
| `POST` | `/api/v1/auth/login` | Authenticate & issue JWT token | None | `OAuth2PasswordRequestForm` / JSON | `200 OK` (`access_token`, `token_type`, `user`) |
| `GET` | `/api/v1/auth/me` | Fetch profile of logged-in user | Bearer JWT | None | `200 OK` |

### 2.2 Search Endpoints (`/api/v1/search`)

| Method | Endpoint | Description | Auth Required | Request Body / Params | Success Status |
|---|---|---|---|---|---|
| `GET` | `/api/v1/search/barcode/{barcode}` | Barcode lookup (DB first, then OFF) | None | Path: `barcode` (string) | `200 OK` |
| `GET` | `/api/v1/search/text` | Search products by name/brand | None | Query: `q` (string), `category_id` (opt), `page` (int), `limit` (int) | `200 OK` (Paginated list) |
| `GET` | `/api/v1/search/history` | Retrieve user search history | Bearer JWT (Optional) | Query: `limit` (default 20) | `200 OK` |

### 2.3 Product Catalog Endpoints (`/api/v1/products`)

| Method | Endpoint | Description | Auth Required | Request Body / Params | Success Status |
|---|---|---|---|---|---|
| `GET` | `/api/v1/products` | Browse product catalog with filters | None | Query: `category`, `health_band`, `sort_by`, `page`, `limit` | `200 OK` |
| `GET` | `/api/v1/products/{product_id}` | Get complete product details | None | Path: `product_id` (UUID) | `200 OK` |
| `GET` | `/api/v1/products/categories` | List all categories & product types | None | None | `200 OK` |
| `POST` | `/api/v1/products` | Add new product manually | Admin JWT | `ProductCreateSchema` | `201 Created` |

### 2.4 Analysis & Scoring Endpoints (`/api/v1/analysis`)

| Method | Endpoint | Description | Auth Required | Request Body / Params | Success Status |
|---|---|---|---|---|---|
| `GET` | `/api/v1/analysis/{product_id}` | Comprehensive nutritional analysis | None | Path: `product_id` (UUID) | `200 OK` |
| `POST` | `/api/v1/analysis/simulate` | On-the-fly score simulation for custom nutrition values | None | `NutrientSimulationRequest` (energy, sugars, etc.) | `200 OK` |

#### Sample Response Payload (`GET /api/v1/analysis/{product_id}`):
```json
{
  "product_id": "8c593a38-6394-4d85-a7b2-04e84b72648d",
  "product_name": "Crunchy Almond Granola",
  "brand": "Nature Valley",
  "category": "breakfast_cereals",
  "product_type": "solid",
  "data_completeness": 0.88,
  
  "scientific_evaluation": {
    "framework": "Nutri-Score 2023 Standard",
    "official_letter_grade": "C",
    "calculated_points": 4,
    "negative_points": {
      "energy": 5,
      "sugars": 6,
      "saturated_fat": 3,
      "salt": 1
    },
    "positive_points": {
      "fiber": 4,
      "protein": 5,
      "fruits_vegetables_nuts": 2
    }
  },

  "proposed_project_score": {
    "framework": "Proposed Project Multi-Parameter Scoring Framework (Academic)",
    "overall_score": 64.2,
    "health_band": "Moderate",
    "confidence_score": 0.88,
    "renormalized": true,
    "missing_parameters": ["added_sugars"],
    "sub_scores": {
      "sugars": { "raw": 18.2, "unit": "g", "sub_score": 48.5, "status": "amber", "weight": 0.25 },
      "sodium": { "raw": 140.0, "unit": "mg", "sub_score": 85.0, "status": "green", "weight": 0.20 },
      "saturated_fat": { "raw": 2.8, "unit": "g", "sub_score": 72.0, "status": "green", "weight": 0.20 },
      "energy": { "raw": 420.0, "unit": "kcal", "sub_score": 52.0, "status": "amber", "weight": 0.14 },
      "fiber": { "raw": 5.4, "unit": "g", "sub_score": 92.0, "status": "green", "weight": 0.11 },
      "protein": { "raw": 9.1, "unit": "g", "sub_score": 80.0, "status": "green", "weight": 0.10 }
    }
  },

  "rule_based_analysis": {
    "nova_group": 3,
    "nova_classification": "Processed food",
    "sugar_rank": 3,
    "sugar_rank_note": "Sugar appears as ingredient #3; moderate penalty applied.",
    "additive_flags": [
      {
        "code": "INS 322",
        "name": "Soy Lecithin",
        "category": "Emulsifier",
        "severity": "info",
        "note": "Common natural emulsifier; no penalty applied."
      }
    ]
  },

  "machine_learning_insights": {
    "predicted_category": "breakfast_cereals",
    "category_model": "TF-IDF + Logistic Regression",
    "prediction_confidence": 0.94
  },

  "explanations": {
    "pros": [
      "Good source of dietary fiber (5.4g per 100g)",
      "Low in sodium (140mg per 100g, well below 600mg cut-off)",
      "Moderate saturated fat content (2.8g per 100g)"
    ],
    "cons": [
      "High in sugar (18.2g per 100g exceeds recommended 15g threshold)",
      "Energy dense (420 kcal per 100g)"
    ]
  }
}
```

### 2.5 Recommendation & Comparison Endpoints (`/api/v1/recommendations`, `/api/v1/comparison`)

| Method | Endpoint | Description | Auth Required | Request Body / Params | Success Status |
|---|---|---|---|---|---|
| `GET` | `/api/v1/recommendations/{product_id}` | Retrieve healthier peer alternatives | None | Query: `limit` (default 5) | `200 OK` |
| `POST` | `/api/v1/comparison` | Side-by-side comparison of 2-4 products | None | `ProductComparisonRequest` (`product_ids`: list of UUIDs) | `200 OK` |

### 2.6 Administration & Config Endpoints (`/api/v1/admin`)

| Method | Endpoint | Description | Auth Required | Request Body / Params | Success Status |
|---|---|---|---|---|---|
| `GET` | `/api/v1/admin/criteria` | List all active scoring criteria & weights | Admin JWT | Query: `product_type` (opt) | `200 OK` |
| `PUT` | `/api/v1/admin/criteria/{id}` | Update scoring thresholds & weights | Admin JWT | `ScoringCriteriaUpdateSchema` | `200 OK` |
| `POST` | `/api/v1/admin/recalculate` | Bulk recalculate cached product scores | Admin JWT | None | `202 Accepted` |
| `GET` | `/api/v1/admin/system-status` | Get DB, cache, and ML model status | Admin JWT | None | `200 OK` |
