import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SavedProductCreate(BaseModel):
    product_id: str
    notes: Optional[str] = None

class SavedProductResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    notes: Optional[str] = None
    saved_at: datetime
    product: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class SearchHistoryResponse(BaseModel):
    id: str
    query_term: str
    query_type: str
    searched_at: datetime
    product_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AdminProductCreate(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    category_id: int
    serving_size: Optional[str] = None
    origin_country: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[Dict[str, Optional[float]]] = None

class AdminProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category_id: Optional[int] = None
    serving_size: Optional[str] = None
    origin_country: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[Dict[str, Optional[float]]] = None

class AdminCategoryCreate(BaseModel):
    name: str
    slug: str
    product_type: str  # 'solid' | 'beverage'
    description: Optional[str] = None
    parent_id: Optional[int] = None

class AdminCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    product_type: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

class ScoringCriteriaParamUpdate(BaseModel):
    weight: float
    t_low: Optional[float] = None
    t_high: Optional[float] = None
    t_target: Optional[float] = None

class ScoringCriteriaUpdate(BaseModel):
    product_type: str  # 'solid' | 'beverage'
    parameters: Dict[str, ScoringCriteriaParamUpdate]

    @field_validator("parameters")
    @classmethod
    def validate_weights(cls, params: Dict[str, ScoringCriteriaParamUpdate]) -> Dict[str, ScoringCriteriaParamUpdate]:
        total_weight = sum(p.weight for p in params.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Parameter weights must sum to 1.0 (received {total_weight:.4f})")
        for k, p in params.items():
            if p.t_low is not None and p.t_high is not None:
                if p.t_low >= p.t_high:
                    raise ValueError(f"For parameter '{k}', t_low ({p.t_low}) must be strictly less than t_high ({p.t_high})")
        return params

class AuditLogResponse(BaseModel):
    id: str
    admin_user_id: Optional[str]
    action: str
    target_entity: str
    target_id: Optional[str]
    changes_json: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
