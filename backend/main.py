from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from api.v1.router import api_router
from core.clients.covenant_registry import close_covenant_registry_clients
from core.clients.rpc import check_rpc_connection
from core.exceptions import (
    FenceAppError,
    UnhandledApplicationError,
)
from core.logging import configure_logging
from core.settings import get_settings
from core.utils.contract_abi import load_registry_abi
from schemas.error import ErrorResponse

settings = get_settings()
configure_logging(settings.log_level.value)
REQUEST_ID_HEADER = "X-Fence-Request-ID"


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
    chain_id = check_rpc_connection(settings.web3_rpc_url)
    logger.info(
        "Connected to RPC {rpc_url} with chain id {chain_id}",
        rpc_url=settings.web3_rpc_url,
        chain_id=chain_id,
    )
    yield
    await close_covenant_registry_clients()
    logger.info("Stopping {app_name}", app_name=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CorrelationIdMiddleware,
    header_name=REQUEST_ID_HEADER,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


def build_error_response(error: FenceAppError) -> JSONResponse:
    """Convert a domain error into the shared API error payload.

    Args:
        error: Application error to expose through the API.

    Returns:
        JSONResponse: Serialized API error response.
    """

    response = JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(
            code=error.code,
            message=error.message,
            details=error.details,
        ).model_dump(),
    )
    if request_id := correlation_id.get():
        response.headers[REQUEST_ID_HEADER] = request_id
    return response


@app.exception_handler(FenceAppError)
async def handle_fence_app_error(
    request: Request,
    exc: FenceAppError,
) -> JSONResponse:
    """Handle registered application errors with one API response shape.

    Args:
        request: Incoming FastAPI request.
        exc: Raised application error.

    Returns:
        JSONResponse: HTTP error response matching the exception status code.
    """

    log = logger.bind(
        error_code=exc.code,
        public_details=exc.details,
        private_details=exc.private_details,
    )
    if exc.status_code >= 500:
        log.opt(exception=exc).error(
            "Request failed with application error {method} {path}",
            method=request.method,
            path=request.url.path,
        )
    else:
        log.warning(
            "Request rejected with application error {method} {path}",
            method=request.method,
            path=request.url.path,
        )
    return build_error_response(exc)


@app.exception_handler(Exception)
async def handle_unregistered_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unregistered exceptions without exposing implementation details.

    Args:
        request: Incoming FastAPI request.
        exc: Unregistered exception raised while serving the request.

    Returns:
        JSONResponse: HTTP 500 error response with the shared error shape.
    """

    logger.opt(exception=exc).error(
        "Request failed with unhandled exception {method} {path}",
        method=request.method,
        path=request.url.path,
    )
    return build_error_response(UnhandledApplicationError())


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
