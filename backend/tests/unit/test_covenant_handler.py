import asyncio
import json
from decimal import Decimal

from business.calculator.dispatcher import CalculatorDispatcher
from business.covenant import CovenantHandler
from business.enums import FacilityType
from core.settings import Settings
from tests.conftest import FakeCovenantRegistryClient


def test_covenant_handler_calculates_result_for_declared_facility() -> None:
    handler = CovenantHandler(
        CalculatorDispatcher(
            Settings(
                educa_covenant_threshold=Decimal("22.0"),
                payearly_covenant_threshold=Decimal("3.0"),
                nomina_covenant_threshold=Decimal("5.0"),
            )
        )
    )
    payload = json.dumps(
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

    result = handler.calculate(
        facility_type=FacilityType.EDUCA,
        payload=payload,
    )

    assert result.computed_effective_rate == 21.5
    assert result.covenant_status == "COMPLIANT"


def test_covenant_handler_publishes_calculated_result() -> None:
    registry_client = FakeCovenantRegistryClient()
    handler = CovenantHandler(
        CalculatorDispatcher(
            Settings(
                educa_covenant_threshold=Decimal("22.0"),
                payearly_covenant_threshold=Decimal("3.0"),
                nomina_covenant_threshold=Decimal("5.0"),
            )
        ),
        registry_client=registry_client,
    )
    payload = json.dumps(
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

    result = asyncio.run(
        handler.calculate_and_publish(
            facility_type=FacilityType.EDUCA,
            payload=payload,
        )
    )

    assert result.computed_effective_rate == 21.5
    assert result.publication.transaction_hash.endswith("1")
