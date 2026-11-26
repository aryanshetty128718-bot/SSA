from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ComparisonProductItem(BaseModel):
    id: str
    barcode: str
    name: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    category_name: str
    overall_score: Optional[float] = None
    score_band: str
    badge_color: str
    nutri_score_grade: Optional[str] = None
    confidence_score: float
    nutrients: Dict[str, Optional[float]]
    sub_scores: Dict[str, Optional[float]]
    pros: List[Dict[str, str]] = Field(default_factory=list)
    cons: List[Dict[str, str]] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)

class ComparisonMatrixItem(BaseModel):
    parameter: str
    display_name: str
    unit: str
    polarity: str  # 'negative' (lower is healthier) or 'positive' (higher is healthier)
    values: Dict[str, Optional[float]]  # barcode -> value
    best_barcode: Optional[str] = None
    summary: str

class ProductComparisonRequest(BaseModel):
    product_ids: Optional[List[str]] = Field(None, description="2 to 4 product UUIDs to compare")
    barcodes: Optional[List[str]] = Field(None, description="2 to 4 product barcodes to compare")

class ProductComparisonResponse(BaseModel):
    products: List[ComparisonProductItem]
    comparison_matrix: List[ComparisonMatrixItem]
    summary_verdict: str
    data_confidence_notes: List[str]
