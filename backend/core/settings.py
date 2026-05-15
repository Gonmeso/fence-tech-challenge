from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Fence Tech Challenge Backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    educa_covenant_threshold: Decimal = Decimal("22.0")
    payearly_covenant_threshold: Decimal = Decimal("3.0")
    nomina_covenant_threshold: Decimal = Decimal("5.0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FENCE_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for the current process.

    Returns:
        Settings: Cached application settings.
    """

    return Settings()
