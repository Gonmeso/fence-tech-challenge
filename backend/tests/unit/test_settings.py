from pytest import MonkeyPatch

from core.settings import LogLevel, Settings


def test_settings_reads_log_level_environment_variable(monkeypatch: MonkeyPatch) -> None:
    """Verify `FENCE_LOG_LEVEL` is parsed into the constrained log-level enum.

    Args:
        monkeypatch: Pytest helper used to set process environment variables.

    Returns:
        None: Asserts settings parsing behavior.
    """

    monkeypatch.setenv("FENCE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv(
        "FENCE_COVENANT_REGISTRY_ADDRESS",
        "0x0000000000000000000000000000000000000001",
    )
    monkeypatch.setenv(
        "FENCE_COVENANT_REGISTRY_PRIVATE_KEY",
        "0x0000000000000000000000000000000000000000000000000000000000000001",
    )

    settings = Settings(
        covenant_registry_address="0x0000000000000000000000000000000000000001",
        covenant_registry_private_key="0x0000000000000000000000000000000000000000000000000000000000000001",
    )

    assert settings.log_level is LogLevel.DEBUG
