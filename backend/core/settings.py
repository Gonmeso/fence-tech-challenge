from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.clients.contract_abi import default_registry_abi_path


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Fence Tech Challenge Backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    educa_covenant_threshold: Decimal = Decimal("22.0")
    payearly_covenant_threshold: Decimal = Decimal("3.0")
    nomina_covenant_threshold: Decimal = Decimal("5.0")
    web3_chain_id: int = 31337
    web3_rpc_url: str = "http://127.0.0.1:8545"
    covenant_registry_address: str | None = None
    covenant_registry_private_key: str | None = None
    covenant_registry_abi_path: Path = default_registry_abi_path()

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
