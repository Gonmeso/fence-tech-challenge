import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        educa_covenant_threshold=Decimal("22.0"),
        payearly_covenant_threshold=Decimal("3.0"),
        nomina_covenant_threshold=Decimal("5.0"),
    )


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"
