from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error payload returned by the API."""

    code: str
    message: str
    details: list[Any]
