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

    settings = Settings()

    assert settings.log_level is LogLevel.DEBUG
