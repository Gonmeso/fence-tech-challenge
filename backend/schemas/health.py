from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Payload returned by the health endpoint."""

    status: str
    app_name: str
    environment: str
