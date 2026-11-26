from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator

# ----------------- User Schemas -----------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "user"

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Category Schemas -----------------
class CategoryBase(BaseModel):
    name: str
    slug: str
    product_type: str  # 'solid' | 'beverage'
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Nutritional Information Schemas -----------------
class NutritionBase(BaseModel):
    energy_kcal: Optional[float] = None
    energy_kj: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    sugars_g: Optional[float] = None
    added_sugars_g: Optional[float] = None
    fiber_g: Optional[float] = None
    proteins_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    salt_g: Optional[float] = None
    fruits_vegetables_nuts_colza_walnut_olive_oils_pct: Optional[float] = None
    basis: str = "per 100g"

class NutritionCreate(NutritionBase):
    pass

class NutritionOut(NutritionBase):
    id: str
    product_id: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Ingredient Schemas -----------------
class IngredientBase(BaseModel):
    canonical_name: str
    ins_number: Optional[str] = None
    is_additive: bool = False
    additive_type: Optional[str] = None
    health_note: Optional[str] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientOut(IngredientBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductIngredientItem(BaseModel):
    ingredient_name: str
    ins_number: Optional[str] = None
    position_order: int
    estimated_percentage: Optional[float] = None
    is_whole_grain: bool = False
    is_allergen: bool = False
    is_additive: bool = False
    additive_type: Optional[str] = None

# ----------------- Scoring Criteria Schemas -----------------
class ScoringCriteriaBase(BaseModel):
    category_id: Optional[int] = None
    product_type: str
    parameter_name: str
    weight: float
    low_threshold: float
    medium_threshold: float
    high_threshold: float
    unit: str
    polarity: str

class ScoringCriteriaCreate(ScoringCriteriaBase):
    pass

class ScoringCriteriaOut(ScoringCriteriaBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Product Schemas -----------------
class ProductBase(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    generic_name: Optional[str] = None
    category_id: int
    serving_size: Optional[str] = None
    image_url: Optional[str] = None
    packaging: Optional[str] = None
    origin_country: Optional[str] = None
    nova_group: Optional[int] = None
    nutri_score_grade: Optional[str] = None
    source: str = "seed"  # 'seed' | 'openfoodfacts' | 'admin'

class ProductCreate(ProductBase):
    nutrition: Optional[NutritionCreate] = None
    ingredients: Optional[List[dict]] = None

class ProductManualEntryIn(BaseModel):
    barcode: str
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = None
    category_id: int
    serving_basis: str = Field("per 100g", pattern="^(per 100g|per 100ml)$")
    serving_size: Optional[str] = None
    energy_kcal: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    sugars_g: Optional[float] = None
    fiber_g: Optional[float] = None
    proteins_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    salt_g: Optional[float] = None
    ingredients_text: Optional[str] = None

    @model_validator(mode="after")
    def validate_nutrition_consistency(self) -> "ProductManualEntryIn":
        # Check non-negative
        for field_name in ["energy_kcal", "fat_g", "saturated_fat_g", "carbohydrates_g", "sugars_g", "fiber_g", "proteins_g", "sodium_mg", "salt_g"]:
            val = getattr(self, field_name)
            if val is not None and val < 0:
                raise ValueError(f"Nutrient '{field_name}' cannot be negative ({val}).")

        # sugars <= carbohydrates
        if self.sugars_g is not None and self.carbohydrates_g is not None:
            if self.sugars_g > self.carbohydrates_g:
                raise ValueError(f"Sugars ({self.sugars_g}g) cannot exceed total carbohydrates ({self.carbohydrates_g}g).")

        # saturated_fat <= fat
        if self.saturated_fat_g is not None and self.fat_g is not None:
            if self.saturated_fat_g > self.fat_g:
                raise ValueError(f"Saturated fat ({self.saturated_fat_g}g) cannot exceed total fat ({self.fat_g}g).")

        # Sync sodium and salt if only one is given
        if self.salt_g is not None and self.sodium_mg is None:
            self.sodium_mg = round((self.salt_g / 2.5) * 1000.0, 1)
        elif self.sodium_mg is not None and self.salt_g is None:
            self.salt_g = round((self.sodium_mg / 1000.0) * 2.5, 3)

        return self

class ProductSummary(ProductBase):
    id: str
    data_completeness_score: float
    data_source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductDetail(ProductSummary):
    category: Optional[CategoryOut] = None
    nutrition: Optional[NutritionOut] = None
    ingredients: List[ProductIngredientItem] = []

    model_config = ConfigDict(from_attributes=True)

# ----------------- Health & Status Schemas -----------------
class HealthCheck(BaseModel):
    status: str
    app_name: str
    environment: str
    database_connected: bool
    version: str = "1.0.0"
    timestamp: datetime

# ----------------- Analysis & Scoring Schemas -----------------
class ParameterExplanation(BaseModel):
    parameter: str
    display_name: str
    raw_value: Optional[float] = None
    unit: str
    band: str
    sub_score: Optional[float] = None
    effective_weight: float
    source: str
    text: str

class ProItem(BaseModel):
    parameter: str
    title: str
    evidence: str

class ConItem(BaseModel):
    parameter: str
    title: str
    evidence: str

class OfficialReferenceOut(BaseModel):
    standard_name: str
    points: Optional[int] = None
    grade: str
    breakdown: Dict[str, Any]
    label: str

class ProductAnalysisOut(BaseModel):
    product_id: str
    barcode: str
    product_name: str
    product_type: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    overall_project_score: Optional[float] = None
    score_band: str
    badge_color: str
    confidence_score: float
    confidence_level: str
    missing_parameters: List[str] = []
    sub_scores: Dict[str, Optional[float]]
    effective_weights: Dict[str, float]
    parameter_explanations: List[ParameterExplanation]
    pros: List[ProItem]
    cons: List[ConItem]
    official_reference: OfficialReferenceOut
    calculated_at: datetime
    scoring_engine_version: str = "1.0.0"
    source: Optional[str] = None
    nutrition: Optional[NutritionOut] = None
    ingredients: Optional[List[ProductIngredientItem]] = None
