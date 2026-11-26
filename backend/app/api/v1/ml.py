from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from app.schemas.ml import (
    ClassificationRequest,
    ClassificationResponse,
    SimilarityRequest,
    SimilarProductItem,
    ModelInfoResponse
)
from app.ml.loader import model_manager

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.post(
    "/classify",
    response_model=ClassificationResponse,
    summary="Predict Product Category using Multimodal ML",
    description="Classifies a product into one of the 10 project categories using multimodal TF-IDF text features and standardized nutrient profiles."
)
def classify_product(payload: ClassificationRequest):
    result = model_manager.classify(
        product_name=payload.product_name,
        brand=payload.brand,
        ingredients_text=payload.ingredients_text,
        nutriments=payload.nutriments
    )
    return result

@router.post(
    "/similar",
    response_model=List[SimilarProductItem],
    summary="Retrieve Multimodal Nearest Neighbor Products",
    description="Retrieves the most similar products from the OFF catalog combining text TF-IDF cosine similarity and nutrient Euclidean distance."
)
def find_similar_products(payload: SimilarityRequest):
    results = model_manager.find_similar(
        product_name=payload.product_name,
        brand=payload.brand,
        ingredients_text=payload.ingredients_text,
        nutriments=payload.nutriments,
        category_filter=payload.category_filter,
        top_k=payload.top_k,
        exclude_code=payload.exclude_code
    )
    return results

@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Get Machine Learning Models Metadata",
    description="Returns training date, architecture, cross-validation metrics, and feature configurations for all loaded ML models."
)
def get_model_info():
    return model_manager.get_info()
