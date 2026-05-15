from fastapi import APIRouter

from api.v1.endpoints.covenant import router as covenant_router
from api.v1.endpoints.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(covenant_router, prefix="/covenants", tags=["covenants"])
