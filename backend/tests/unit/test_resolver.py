import json
from decimal import Decimal

import pytest

from business.calculator import (
    CalculatorResolver,
    EducaCalculator,
    NominaCalculator,
    PayearlyCalculator,
)
from business.enums import FacilityType
from core.exceptions import (
    FacilityPayloadValidationError,
    InvalidJsonPayloadError,
    InvalidPayloadTypeError,
)
from core.settings import Settings


def test_resolver_returns_educa_calculator_for_educa_payload() -> None:
    resolver = CalculatorResolver(
        Settings(
            educa_covenant_threshold=Decimal("21.5"),
            payearly_covenant_threshold=Decimal("3.0"),
            nomina_covenant_threshold=Decimal("5.0"),
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
                "disbursement_amount": 6500.0,
                "outstanding_amount": 4875.0,
                "repaid_amount": 1625.0,
                "interest_rate_percentage": 20.86,
                "days_past_due": 0,
                "country": "ES",
                "amount": 6500.0,
            }
        ]
    )

    resolved = resolver.resolve(
        facility_type=FacilityType.EDUCA,
        payload=payload,
    )

    assert resolved.facility_type == FacilityType.EDUCA
    assert isinstance(resolved.calculator, EducaCalculator)
    assert resolved.calculator.threshold == Decimal("21.5")


def test_resolver_returns_payearly_calculator_for_payearly_payload() -> None:
    resolver = CalculatorResolver(Settings())
    payload = [
        {
            "external_id": "PAY-1",
            "created_at": "2025-06-15T09:00:00+00:00",
            "due_date": "2026-03-15",
            "last_updated": "2026-01-20T17:23:11.783Z",
            "status": "performing",
            "is_eligible": True,
            "employer_id": "EMP-1",
            "employer_name": "Employer",
            "employee_id": "USER-1",
            "user_state": "WI",
            "total_principal_amount": 8500.0,
            "outstanding_principal_amount": 3400.0,
            "repaid_principal_amount": 5100.0,
            "total_fee_amount": 1.75,
            "outstanding_fee_amount": 1.75,
            "receivable_currency": "USD",
            "days_past_due": 0,
            "amount": 8500.0,
        }
    ]

    calculator = resolver.resolve(
        facility_type=FacilityType.PAYEARLY,
        payload=payload,
    ).calculator

    assert isinstance(calculator, PayearlyCalculator)
    assert calculator.threshold == Decimal("3.0")


def test_resolver_returns_nomina_calculator_for_nomina_payload() -> None:
    resolver = CalculatorResolver(Settings())
    payload = json.dumps(
        [
            {
                "external_id": "NOM-1",
                "origination_date": "2024-05-31",
                "cutoff_date": "2026-01-15",
                "status": "active",
                "is_eligible": True,
                "employer_name": "Employer",
                "employer_tax_id": "ESA00000001",
                "net_monthly_salary": 3200.0,
                "advance_amount": 1800.0,
                "outstanding_amount": 900.0,
                "repaid_amount": 900.0,
                "fee_percentage": 2.5,
                "fee_amount": 45.0,
                "days_past_due": 0,
                "maturity_date": "31/01/2025",
                "amount": 1800.0,
            }
        ]
    )

    resolved = resolver.resolve(
        facility_type=FacilityType.NOMINA,
        payload=payload,
    )

    assert resolved.facility_type == FacilityType.NOMINA
    assert isinstance(resolved.calculator, NominaCalculator)
    assert resolved.calculator.threshold == Decimal("5.0")


def test_resolver_rejects_invalid_json() -> None:
    resolver = CalculatorResolver(Settings())

    with pytest.raises(InvalidJsonPayloadError, match="Payload is not valid JSON"):
        resolver.resolve(
            facility_type=FacilityType.EDUCA,
            payload="{not-json}",
        )


def test_resolver_rejects_invalid_utf8_bytes() -> None:
    resolver = CalculatorResolver(Settings())

    with pytest.raises(InvalidJsonPayloadError, match="Payload is not valid JSON"):
        resolver.resolve(
            facility_type=FacilityType.EDUCA,
            payload=b"\xff",
        )


def test_resolver_rejects_non_array_json() -> None:
    resolver = CalculatorResolver(Settings())

    with pytest.raises(InvalidPayloadTypeError, match="Payload must be a JSON array"):
        resolver.resolve(
            facility_type=FacilityType.EDUCA,
            payload='{"external_id":"EDU-1"}',
        )


def test_resolver_rejects_payload_for_declared_facility() -> None:
    resolver = CalculatorResolver(Settings())
    payload = json.dumps(
        [
            {
                "external_id": "UNKNOWN-1",
                "status": "open",
                "is_eligible": True,
                "days_past_due": 0,
                "amount": 10,
            }
        ]
    )

    with pytest.raises(
        FacilityPayloadValidationError,
        match="Payload does not match the declared facility schema",
    ):
        resolver.resolve(
            facility_type=FacilityType.EDUCA,
            payload=payload,
        )
