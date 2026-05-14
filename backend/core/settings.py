from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fence Tech Challenge Backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FENCE_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
