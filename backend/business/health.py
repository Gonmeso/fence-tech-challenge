from core.settings import Settings
from schemas.health import HealthResponse


class HealthHandler:
    """Build the health response returned by the API."""

    def __init__(self, settings: Settings) -> None:
        """Store application settings exposed by the health endpoint.

        Args:
            settings: Application settings to surface in the response.
        """

        self._settings = settings

    def get_health(self) -> HealthResponse:
        """Return the current application status payload.

        Returns:
            HealthResponse: Current application health information.
        """

        return HealthResponse(
            status="ok",
            app_name=self._settings.app_name,
            environment=self._settings.environment,
        )
