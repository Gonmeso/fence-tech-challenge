from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from api.v1.router import api_router
from core.logging import configure_logging
from core.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Starting {app_name} in {environment} mode",
        app_name=settings.app_name,
        environment=settings.environment,
    )
    yield
    logger.info("Stopping {app_name}", app_name=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "message": f"{settings.app_name} is running",
        "docs_url": "/docs",
    }
