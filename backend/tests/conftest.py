import os
import sys
from collections.abc import Iterator
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault(
    "FENCE_COVENANT_REGISTRY_ADDRESS",
    "0x0000000000000000000000000000000000000001",
)
os.environ.setdefault(
    "FENCE_COVENANT_REGISTRY_PRIVATE_KEY",
    "0x0000000000000000000000000000000000000000000000000000000000000001",
)

import api.v1.endpoints.health as health_endpoint
import main as app_module
from api.deps import get_covenant_handler
from business.calculator.resolver import CalculatorResolver
from business.covenant import CovenantHandler
from business.enums import FacilityType
from core.exceptions import CovenantReportNotFoundError
from core.settings import Settings, SettingsConfigDict
from main import app
from schemas.covenant import (
    CovenantPublication,
    CovenantResult,
    CovenantSummary,
    ExcludedAsset,
    OnChainCovenantResult,
)


class FakeCovenantRegistryClient:
    """In-memory contract client for API tests."""

    chain_id = 31337
    contract_address = "0x0000000000000000000000000000000000000001"

    def __init__(self) -> None:
        """Initialize empty reports.

        Returns:
            None: Initializes the fake client.
        """

        self._reports: dict[FacilityType, OnChainCovenantResult] = {}
        self._transaction_count = 0

    async def publish_facility_report(
        self,
        *,
        facility_type: FacilityType,
        result: CovenantResult,
    ) -> CovenantPublication:
        """Store a report in memory.

        Args:
            facility_type: Facility associated with the report.
            result: Calculated covenant result.

        Returns:
            CovenantPublication: Fake transaction metadata.
        """

        self._transaction_count += 1
        transaction_hash = f"0x{self._transaction_count:064x}"
        effective_rate_bps = int(
            (result.computed_effective_rate * Decimal("100")).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )
        self._reports[facility_type] = OnChainCovenantResult(
            facility=facility_type.value,
            effective_rate_bps=effective_rate_bps,
            computed_effective_rate=Decimal(effective_rate_bps) / Decimal("100"),
            covenant_status=result.covenant_status,
            summary=CovenantSummary(
                total_assets_evaluated=result.summary.total_assets_evaluated,
                assets_included=result.summary.assets_included,
                assets_excluded=result.summary.assets_excluded,
            ),
            included_assets=result.included_assets,
            excluded_assets=[
                ExcludedAsset(
                    external_id=asset.external_id,
                    reasons=list(asset.reasons),
                )
                for asset in result.excluded_assets
            ],
            updated_at=self._transaction_count,
            exists=True,
            chain_id=self.chain_id,
            contract_address=self.contract_address,
        )
        return CovenantPublication(
            chain_id=self.chain_id,
            contract_address=self.contract_address,
            transaction_hash=transaction_hash,
        )

    async def get_facility_report(self, *, facility_type: FacilityType) -> OnChainCovenantResult:
        """Read a report from memory.

        Args:
            facility_type: Facility requested by the caller.

        Raises:
            CovenantReportNotFoundError: If no report has been stored.

        Returns:
            OnChainCovenantResult: Stored report.
        """

        try:
            return self._reports[facility_type]
        except KeyError as exc:
            raise CovenantReportNotFoundError(facility_type=facility_type) from exc


@pytest.fixture
def settings() -> Settings:
    return Settings(
        educa_covenant_threshold=Decimal("22.0"),
        payearly_covenant_threshold=Decimal("3.0"),
        nomina_covenant_threshold=Decimal("5.0"),
        covenant_registry_address="0x0000000000000000000000000000000000000001",
        covenant_registry_private_key="0x0000000000000000000000000000000000000000000000000000000000000001",
    )


@pytest.fixture
def fake_registry_client() -> FakeCovenantRegistryClient:
    return FakeCovenantRegistryClient()


@pytest.fixture
def test_settings() -> Settings:
    """Return explicit settings that do not load values from `.env`.

    Returns:
        Settings: Test-only settings with stable defaults.
    """

    class TestSettings(Settings):
        """Settings subclass that never reads from `.env`."""

        model_config = SettingsConfigDict(
            env_file=None,
            env_prefix="FENCE_",
            case_sensitive=False,
        )

    return TestSettings(
        educa_covenant_threshold=Decimal("22.0"),
        payearly_covenant_threshold=Decimal("3.0"),
        nomina_covenant_threshold=Decimal("5.0"),
        covenant_registry_address="0x0000000000000000000000000000000000000001",
        covenant_registry_private_key="0x0000000000000000000000000000000000000000000000000000000000000001",
    )


@pytest.fixture
def test_app(
    monkeypatch: pytest.MonkeyPatch,
    test_settings: Settings,
    fake_registry_client: FakeCovenantRegistryClient,
) -> Iterator[TestClient]:
    """Build a FastAPI test client that ignores local `.env` files.

    Args:
        monkeypatch: Pytest helper for patching module state.
        test_settings: Explicit settings fixture that bypasses `.env`.
        fake_registry_client: In-memory registry client used by API tests.

    Returns:
        Iterator[TestClient]: FastAPI client with isolated settings.
    """

    def build_handler() -> CovenantHandler:
        return CovenantHandler(
            resolver=CalculatorResolver(test_settings),
            registry_client=fake_registry_client,
        )

    monkeypatch.setattr(app_module, "settings", test_settings)
    monkeypatch.setattr(app_module, "get_settings", lambda: test_settings)
    monkeypatch.setattr(app_module, "check_rpc_connection", lambda *_args, **_kwargs: 31337)
    monkeypatch.setattr(health_endpoint, "get_settings", lambda: test_settings)
    app.dependency_overrides[get_covenant_handler] = build_handler
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def api_client(
    settings: Settings,
    fake_registry_client: FakeCovenantRegistryClient,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    def build_handler() -> CovenantHandler:
        return CovenantHandler(
            resolver=CalculatorResolver(settings),
            registry_client=fake_registry_client,
        )

    monkeypatch.setattr(app_module, "check_rpc_connection", lambda *_args, **_kwargs: 31337)
    app.dependency_overrides[get_covenant_handler] = build_handler
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"
