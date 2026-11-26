import os
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field

# Locate base directory and .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

def load_env_file(path: Path):
    """Load key-value pairs from .env file into os.environ if present."""
    if not path.is_file():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val

load_env_file(ENV_PATH)

def _resolve_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL", "sqlite:///./smart_shopping.db")
    if raw_url.startswith("sqlite:///./") or raw_url == "sqlite:///smart_shopping.db":
        db_file = (BASE_DIR / "smart_shopping.db").resolve()
        return f"sqlite:///{db_file.as_posix()}"
    return raw_url

class Settings(BaseModel):
    APP_NAME: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Smart Shopping Assistant"))
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True").lower() in ("true", "1", "yes"))
    API_V1_PREFIX: str = Field(default_factory=lambda: os.getenv("API_V1_PREFIX", "/api/v1"))
    
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "super-secret-key-mca-project-2026"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY in ("super-secret-key-mca-project-2026", "change-this-ultra-secure-secret-key-for-mca-project-evaluation-2026", ""):
                raise RuntimeError("CRITICAL SECURITY ERROR: In production mode, SECRET_KEY must be set to a cryptographically secure random secret in .env.")
    
    # Database URL: default to SQLite anchored at BASE_DIR for quick dev/demo
    DATABASE_URL: str = Field(default_factory=_resolve_database_url)
    
    # External API: Open Food Facts
    OPEN_FOOD_FACTS_BASE_URL: str = Field(default_factory=lambda: os.getenv("OPEN_FOOD_FACTS_BASE_URL", "https://world.openfoodfacts.org"))
    OPEN_FOOD_FACTS_TIMEOUT_SECONDS: float = Field(default_factory=lambda: float(os.getenv("OPEN_FOOD_FACTS_TIMEOUT_SECONDS", "8.0")))
    USER_AGENT: str = Field(default_factory=lambda: os.getenv("USER_AGENT", "SmartShoppingAssistant/1.0 (MCA Project)"))
    
    # CORS Origins
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            origin.strip() 
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",")
            if origin.strip()
        ]
    )

    # Recommendations Configuration
    INCLUDE_SEED_IN_RECOMMENDATIONS: bool = Field(
        default_factory=lambda: os.getenv("INCLUDE_SEED_IN_RECOMMENDATIONS", "False").lower() in ("true", "1", "yes")
    )
    RECOMMENDATION_MIN_SIMILARITY: float = Field(default_factory=lambda: float(os.getenv("RECOMMENDATION_MIN_SIMILARITY", "0.08")))
    RECOMMENDATION_MIN_COMPLETENESS: float = Field(default_factory=lambda: float(os.getenv("RECOMMENDATION_MIN_COMPLETENESS", "80.0")))

    # Allowed Related Categories Mapping for Category Coherence Gate
    ALLOWED_RELATED_CATEGORIES: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "breakfast-cereals": ["breakfast-cereals"],
            "sweet-spreads-nut-butters": ["sweet-spreads-nut-butters"],
            "chocolates-confectionery": ["chocolates-confectionery"],
            "soft-drinks-sodas": ["soft-drinks-sodas", "fruit-juices"],
            "fruit-juices": ["fruit-juices", "soft-drinks-sodas"],
            "dairy-plant-drinks": ["dairy-plant-drinks"],
            "yoghurts": ["yoghurts"],
            "biscuits-cookies": ["biscuits-cookies"],
            "breads-bakery": ["breads-bakery"],
            "chips-crisps": ["chips-crisps"],
            "instant-noodles-pasta": ["instant-noodles-pasta"],
            "other": ["other"]
        }
    )

    # Keywords strictly disqualified from solid food alternative recommendations
    NON_COMPARABLE_FOOD_KEYWORDS: List[str] = Field(
        default_factory=lambda: [
            "chewing gum", "chewing-gum", "bubble gum", "bubblegum", "goma de mascar", "mascar",
            "gum", "gums", "mint", "mints", "pastille", "pastilles", "breath freshener",
            "candy", "hard candy", "lollipop", "sweetener", "lozenges",
            "drops", "cough drops", "licorice", "regaliz"
        ]
    )

settings = Settings()
