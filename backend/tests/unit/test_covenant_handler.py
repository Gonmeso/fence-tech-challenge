import asyncio
import json
import threading
from decimal import Decimal

from business.calculator.resolver import CalculatorResolver
from business.covenant import CovenantHandler
from business.enums import FacilityType
from core.settings import Settings
from schemas.covenant import CovenantResult
from tests.conftest import FakeCovenantRegistryClient


def build_handler(
    registry_client: FakeCovenantRegistryClient | None = None,
) -> CovenantHandler:
    """Build a covenant handler with stable test thresholds.

    Args:
        registry_client: Optional fake registry client for publication tests.

    Returns:
        CovenantHandler: Handler wired for unit tests.
    """

    return CovenantHandler(
        CalculatorResolver(
            Settings(
                educa_covenant_threshold=Decimal("22.0"),
                payearly_covenant_threshold=Decimal("3.0"),
                nomina_covenant_threshold=Decimal("5.0"),
            )
        ),
        registry_client=registry_client,
    )


class RecordingCovenantHandler(CovenantHandler):
    """Covenant handler that records calculation thread ids for tests."""

    def __init__(
        self,
        resolver: CalculatorResolver,
        registry_client: FakeCovenantRegistryClient,
    ) -> None:
        """Store the resolver, registry client, and thread id captures.

        Args:
            resolver: Resolver used by the parent handler.
            registry_client: Fake registry client used by the parent handler.
        """

        super().__init__(resolver=resolver, registry_client=registry_client)
        self.calculation_thread_ids: list[int] = []

    def calculate(
        self,
        *,
        facility_type: FacilityType,
        payload: str | bytes | list[dict[str, object]],
    ) -> CovenantResult:
        """Record the current thread before delegating to the parent calculation.

        Args:
            facility_type: Facility declared by the test.
            payload: Test payload passed through to the parent handler.

        Returns:
            CovenantResult: Calculated covenant result.
        """

        self.calculation_thread_ids.append(threading.get_ident())
        return super().calculate(facility_type=facility_type, payload=payload)


def educa_payload() -> str:
    """Build a valid single-asset Educa payload.

    Returns:
        str: Serialized Educa payload.
    """

    return json.dumps(
        [
            {
                "external_id": "EDU-1",
                "effective_date": "2024-06-25",
                "reporting_date": "2026-01-15",
                "status": "open",
                "is_eligible": True,
                "student_id": "STU-1",
                "school_id": "SCH-1",
                "loan_status": "current",
                "disbursement_amount": 1000,
                "outstanding_amount": 1000,
                "repaid_amount": 0,
                "interest_rate_percentage": 21.5,
                "days_past_due": 0,
                "country": "ES",
                "amount": 1000,
            }
        ]
    )


def test_covenant_handler_calculates_result_for_declared_facility() -> None:
    handler = build_handler()

    result = handler.calculate(
        facility_type=FacilityType.EDUCA,
        payload=educa_payload(),
    )

    assert result.computed_effective_rate == Decimal("21.50")
    assert result.covenant_status == "COMPLIANT"


def test_covenant_handler_publish_publishes_existing_result() -> None:
    registry_client = FakeCovenantRegistryClient()
    handler = build_handler(registry_client)
    result = handler.calculate(
        facility_type=FacilityType.EDUCA,
        payload=educa_payload(),
    )

    published = asyncio.run(
        handler.publish(
            facility_type=FacilityType.EDUCA,
            result=result,
        )
    )

    assert published.computed_effective_rate == Decimal("21.50")
    assert published.publication.transaction_hash.endswith("1")


def test_covenant_handler_calculate_and_publish_runs_calculation_in_worker_thread() -> None:
    registry_client = FakeCovenantRegistryClient()
    handler = RecordingCovenantHandler(
        resolver=CalculatorResolver(
            Settings(
                educa_covenant_threshold=Decimal("22.0"),
                payearly_covenant_threshold=Decimal("3.0"),
                nomina_covenant_threshold=Decimal("5.0"),
            )
        ),
        registry_client=registry_client,
    )
    main_thread_id = threading.get_ident()

    published = asyncio.run(
        handler.calculate_and_publish(
            facility_type=FacilityType.EDUCA,
            payload=educa_payload(),
        )
    )

    assert handler.calculation_thread_ids
    assert handler.calculation_thread_ids[0] != main_thread_id
    assert published.computed_effective_rate == Decimal("21.50")
    assert published.publication.transaction_hash.endswith("1")


def test_covenant_handler_calculate_and_publish_publishes_calculated_result() -> None:
    registry_client = FakeCovenantRegistryClient()
    handler = build_handler(registry_client)

    result = asyncio.run(
        handler.calculate_and_publish(
            facility_type=FacilityType.EDUCA,
            payload=educa_payload(),
        )
    )

    assert result.computed_effective_rate == Decimal("21.50")
    assert result.publication.transaction_hash.endswith("1")
