from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ClassificationRequest(BaseModel):
    product_name: str = Field(..., description="Product commercial title or description", min_length=1)
    brand: Optional[str] = Field(None, description="Product brand name")
    ingredients_text: Optional[str] = Field(None, description="Raw ingredient listing text")
    nutriments: Optional[Dict[str, Optional[float]]] = Field(
        default=None,
        description="Nutritional dictionary per 100g/100ml (energy-kcal_100g, sugars_100g, fat_100g, etc.)"
    )

class ClassificationResponse(BaseModel):
    predicted_category: str = Field(..., description="Project category identifier")
    confidence: float = Field(..., description="Model classification confidence between 0.0 and 1.0")
    probabilities: Dict[str, float] = Field(default_factory=dict, description="Per-class probability distribution")
    model_type: str = Field("ML prediction", description="Execution mode: 'ML prediction' or 'heuristic fallback'")
    model_name: str = Field(..., description="Identifier of the model used (e.g. 'LinearSVM', 'Keyword Rules')")
    features_used: List[str] = Field(default_factory=list, description="Feature modalities ingested by the model")

class SimilarityRequest(BaseModel):
    product_name: str = Field(..., description="Query product title", min_length=1)
    brand: Optional[str] = Field(None, description="Query product brand")
    ingredients_text: Optional[str] = Field(None, description="Query ingredients list")
    nutriments: Optional[Dict[str, Optional[float]]] = Field(
        default=None,
        description="Query product nutrients (7-dim vector)"
    )
    category_filter: Optional[str] = Field(None, description="Optional category restriction")
    top_k: int = Field(5, ge=1, le=20, description="Number of nearest neighbors to retrieve")
    exclude_code: Optional[str] = Field(None, description="Barcode of query product to exclude from self-matches")

class SimilarProductItem(BaseModel):
    rank: int
    code: str
    product_name: str
    brand: Optional[str] = None
    category: str
    hybrid_similarity: float
    text_similarity: float
    nutrient_similarity: float
    model_type: str = "ML prediction"

class ModelInfoResponse(BaseModel):
    classifier: Dict[str, Any]
    similarity_engine: Dict[str, Any]
