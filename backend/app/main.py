from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import logger
from app.core.exceptions import (
    SSABaseException,
    ssa_domain_exception_handler,
    global_unhandled_exception_handler
)
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.ml import router as ml_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.compare import router as compare_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup logic
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' mode...")
    logger.info(f"Connected DB target: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    yield
    # Application shutdown logic
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Based Food and Beverage Analysis and Healthier-Alternative Recommendation API (Academic MCA Project)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom and global exception handlers
app.add_exception_handler(SSABaseException, ssa_domain_exception_handler)
app.add_exception_handler(Exception, global_unhandled_exception_handler)

# Include Routers
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX)
app.include_router(ml_router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendations_router, prefix=settings.API_V1_PREFIX)
app.include_router(compare_router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Root"])
def root_endpoint():
    return {
        "message": f"Welcome to the {settings.APP_NAME} API",
        "documentation": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "health_check": f"{settings.API_V1_PREFIX}/health"
    }
