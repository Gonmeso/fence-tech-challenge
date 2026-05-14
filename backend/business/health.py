from core.settings import Settings
from schemas.health import HealthResponse


class HealthHandler:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            app_name=self._settings.app_name,
            environment=self._settings.environment,
        )
