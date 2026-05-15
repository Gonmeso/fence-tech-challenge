from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from api.v1.router import api_router
from core.exceptions import (
    CalculatorExecutionError,
    FacilityPayloadValidationError,
    FenceAppError,
    InvalidFacilityHeaderError,
    InvalidJsonPayloadError,
    InvalidPayloadTypeError,
    MissingFacilityHeaderError,
    UnsupportedFacilityError,
)
from core.logging import configure_logging
from core.settings import get_settings
from schemas.error import ErrorResponse

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


# TODO: This should be refactored, we should have specific HTTP errors, then spcefic domain errors, which then can be mappe to the HTTP errors. This way we can have more specific error handling and avoid having to catch all errors in the same way. We can also have a more specific error response model for each type of error, which can include additional fields that are relevant for that type of error.
def build_error_response(error: FenceAppError, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            code=error.code,
            message=error.message,
            details=error.details,
        ).model_dump(),
    )


@app.exception_handler(MissingFacilityHeaderError)
async def handle_missing_facility_header(
    _: Request,
    exc: MissingFacilityHeaderError,
) -> JSONResponse:
    return build_error_response(exc, 400)


@app.exception_handler(InvalidFacilityHeaderError)
async def handle_invalid_facility_header(
    _: Request,
    exc: InvalidFacilityHeaderError,
) -> JSONResponse:
    return build_error_response(exc, 400)


@app.exception_handler(InvalidJsonPayloadError)
async def handle_invalid_json_payload(
    _: Request,
    exc: InvalidJsonPayloadError,
) -> JSONResponse:
    return build_error_response(exc, 400)


@app.exception_handler(InvalidPayloadTypeError)
async def handle_invalid_payload_type(
    _: Request,
    exc: InvalidPayloadTypeError,
) -> JSONResponse:
    return build_error_response(exc, 400)


@app.exception_handler(UnsupportedFacilityError)
async def handle_unsupported_facility(
    _: Request,
    exc: UnsupportedFacilityError,
) -> JSONResponse:
    return build_error_response(exc, 400)


@app.exception_handler(FacilityPayloadValidationError)
async def handle_facility_payload_validation(
    _: Request,
    exc: FacilityPayloadValidationError,
) -> JSONResponse:
    return build_error_response(exc, 422)


@app.exception_handler(CalculatorExecutionError)
async def handle_calculator_execution(
    _: Request,
    exc: CalculatorExecutionError,
) -> JSONResponse:
    return build_error_response(exc, 500)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "message": f"{settings.app_name} is running",
        "docs_url": "/docs",
    }
