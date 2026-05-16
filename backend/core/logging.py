import logging
import sys
from typing import Any

from asgi_correlation_id import correlation_id
from loguru import logger


class InterceptHandler(logging.Handler):
    """Forward standard-library logs to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Re-emit a standard log record through Loguru.

        Args:
            record: Log record emitted by the stdlib logging subsystem.

        Returns:
            None: Writes the record through Loguru.
        """

        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        # Walk back out of the logging module so Loguru reports the original
        # caller instead of this bridge handler.
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def configure_logging(log_level: str) -> None:
    """Configure Loguru and bridge framework logs into it.

    Args:
        log_level: Minimum log level to emit.

    Returns:
        None: Configures process-wide logging handlers.
    """

    logger.remove()
    logger.configure(patcher=_add_request_id)
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "[{extra[request_id]}] | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False


def _add_request_id(record: Any) -> None:
    """Attach the active request id to every Loguru record.

    Args:
        record: Loguru record that will be formatted.

    Returns:
        None: Mutates the record in place.
    """

    extra = record["extra"]
    if isinstance(extra, dict):
        extra["request_id"] = correlation_id.get() or "-"
