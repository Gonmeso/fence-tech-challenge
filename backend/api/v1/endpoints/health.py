from fastapi import APIRouter

from business.health import HealthHandler
from core.settings import get_settings
from schemas.health import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthHandler(get_settings()).get_health()
