from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from api.v1.router import api_router
from core.clients.contract_abi import load_registry_abi
from core.exceptions import (
    CalculatorExecutionError,
    CovenantPublicationError,
    CovenantRegistryConfigurationError,
    CovenantRegistryReadError,
    CovenantReportNotFoundError,
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
    """Log application startup and shutdown events.

    Args:
        _: FastAPI application instance managed by FastAPI.

    Yields:
        None: Control back to FastAPI while the application is running.
    """

    logger.info(
        "Starting {app_name} in {environment} mode",
        app_name=settings.app_name,
        environment=settings.environment,
    )
    load_registry_abi(settings.covenant_registry_abi_path)
    yield
    logger.info("Stopping {app_name}", app_name=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


# TODO: Split domain errors from HTTP mapping as the error model grows.
def build_error_response(error: FenceAppError, status_code: int) -> JSONResponse:
    """Convert a domain error into the shared API error payload.

    Args:
        error: Application error to expose through the API.
        status_code: HTTP status code to return with the payload.

    Returns:
        JSONResponse: Serialized API error response.
    """

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
    """Handle requests that do not declare a facility header.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 400 error response.
    """

    return build_error_response(exc, 400)


@app.exception_handler(InvalidFacilityHeaderError)
async def handle_invalid_facility_header(
    _: Request,
    exc: InvalidFacilityHeaderError,
) -> JSONResponse:
    """Handle requests with an invalid facility header.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 400 error response.
    """

    return build_error_response(exc, 400)


@app.exception_handler(InvalidJsonPayloadError)
async def handle_invalid_json_payload(
    _: Request,
    exc: InvalidJsonPayloadError,
) -> JSONResponse:
    """Handle requests with malformed JSON bodies.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 400 error response.
    """

    return build_error_response(exc, 400)


@app.exception_handler(InvalidPayloadTypeError)
async def handle_invalid_payload_type(
    _: Request,
    exc: InvalidPayloadTypeError,
) -> JSONResponse:
    """Handle requests whose payload is not a JSON array.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 400 error response.
    """

    return build_error_response(exc, 400)


@app.exception_handler(UnsupportedFacilityError)
async def handle_unsupported_facility(
    _: Request,
    exc: UnsupportedFacilityError,
) -> JSONResponse:
    """Handle requests for unsupported facilities.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 400 error response.
    """

    return build_error_response(exc, 400)


@app.exception_handler(FacilityPayloadValidationError)
async def handle_facility_payload_validation(
    _: Request,
    exc: FacilityPayloadValidationError,
) -> JSONResponse:
    """Handle payloads that fail facility schema validation.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 422 error response.
    """

    return build_error_response(exc, 422)


@app.exception_handler(CalculatorExecutionError)
async def handle_calculator_execution(
    _: Request,
    exc: CalculatorExecutionError,
) -> JSONResponse:
    """Handle unexpected calculator execution failures.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 500 error response.
    """

    return build_error_response(exc, 500)


@app.exception_handler(CovenantRegistryConfigurationError)
async def handle_covenant_registry_configuration(
    _: Request,
    exc: CovenantRegistryConfigurationError,
) -> JSONResponse:
    """Handle missing or invalid smart contract configuration.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 500 error response.
    """

    return build_error_response(exc, 500)


@app.exception_handler(CovenantPublicationError)
async def handle_covenant_publication(
    _: Request,
    exc: CovenantPublicationError,
) -> JSONResponse:
    """Handle smart contract publication failures.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 500 error response.
    """

    return build_error_response(exc, 500)


@app.exception_handler(CovenantReportNotFoundError)
async def handle_covenant_report_not_found(
    _: Request,
    exc: CovenantReportNotFoundError,
) -> JSONResponse:
    """Handle missing on-chain covenant reports.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 404 error response.
    """

    return build_error_response(exc, 404)


@app.exception_handler(CovenantRegistryReadError)
async def handle_covenant_registry_read(
    _: Request,
    exc: CovenantRegistryReadError,
) -> JSONResponse:
    """Handle smart contract read failures.

    Args:
        _: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP 500 error response.
    """

    return build_error_response(exc, 500)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Return a small metadata payload for local sanity checks.

    Returns:
        dict[str, str]: Application status and docs link.
    """

    return {
        "message": f"{settings.app_name} is running",
        "docs_url": "/docs",
    }
