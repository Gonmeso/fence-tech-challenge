from decimal import Decimal

from business.calculator import EducaCalculator, NominaCalculator, PayearlyCalculator
from schemas.covenant import CovenantStatus
from schemas.educa import EducaPortfolio
from schemas.nomina import NominaPortfolio
from schemas.payearly import PayearlyPortfolio


def test_educa_calculator_returns_breach_when_threshold_is_met() -> None:
    portfolio = EducaPortfolio.model_validate(
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
                "interest_rate_percentage": 22.0,
                "days_past_due": 0,
                "country": "ES",
                "amount": 1000,
            }
        ]
    )

    result = EducaCalculator(Decimal("22.0")).calculate(portfolio)

    assert result.computed_effective_rate == 22.0
    assert result.covenant_status == CovenantStatus.BREACH


def test_educa_calculator_handles_no_eligible_assets() -> None:
    portfolio = EducaPortfolio.model_validate(
        [
            {
                "external_id": "EDU-1",
                "effective_date": "2024-06-25",
                "reporting_date": "2026-01-15",
                "status": "closed",
                "is_eligible": False,
                "student_id": "STU-1",
                "school_id": "SCH-1",
                "loan_status": "written_off",
                "disbursement_amount": 1000,
                "outstanding_amount": 1000,
                "repaid_amount": 0,
                "interest_rate_percentage": 22.0,
                "days_past_due": 0,
                "country": "ES",
                "amount": 1000,
            }
        ]
    )

    result = EducaCalculator(Decimal("22.0")).calculate(portfolio)

    assert result.computed_effective_rate == 0.0
    assert result.summary.assets_included == 0
    assert result.summary.assets_excluded == 1


def test_payearly_calculator_uses_threshold_to_mark_breach() -> None:
    portfolio = PayearlyPortfolio.model_validate(
        [
            {
                "external_id": "PAY-1",
                "created_at": "2025-01-01T00:00:00+00:00",
                "due_date": "2025-01-31",
                "last_updated": "2025-01-15T00:00:00+00:00",
                "status": "performing",
                "is_eligible": True,
                "employer_id": "EMP-1",
                "employer_name": "Employer",
                "employee_id": "USER-1",
                "user_state": "TX",
                "total_principal_amount": 1000,
                "outstanding_principal_amount": 1000,
                "repaid_principal_amount": 0,
                "total_fee_amount": 10,
                "outstanding_fee_amount": 10,
                "receivable_currency": "USD",
                "days_past_due": 0,
                "amount": 1000,
            }
        ]
    )

    result = PayearlyCalculator(Decimal("0.1")).calculate(portfolio)

    assert result.computed_effective_rate > 0.1
    assert result.covenant_status == CovenantStatus.BREACH


def test_nomina_calculator_uses_threshold_to_mark_compliant() -> None:
    portfolio = NominaPortfolio.model_validate(
        [
            {
                "external_id": "NOM-1",
                "origination_date": "2024-01-01",
                "cutoff_date": "2024-06-01",
                "status": "active",
                "is_eligible": True,
                "employer_name": "Employer",
                "employer_tax_id": "ESA00000001",
                "net_monthly_salary": 3000,
                "advance_amount": 1000,
                "outstanding_amount": 1000,
                "repaid_amount": 0,
                "fee_percentage": 2,
                "fee_amount": 20,
                "days_past_due": 0,
                "maturity_date": "01/07/2024",
                "amount": 1000,
            }
        ]
    )

    result = NominaCalculator(Decimal("20.0")).calculate(portfolio)

    assert result.computed_effective_rate == 4.0
    assert result.covenant_status == CovenantStatus.COMPLIANT


def test_calculators_capture_excluded_assets_and_reasons() -> None:
    portfolio = PayearlyPortfolio.model_validate(
        [
            {
                "external_id": "PAY-1",
                "created_at": "2025-01-01T00:00:00+00:00",
                "due_date": "2025-01-31",
                "last_updated": "2025-01-15T00:00:00+00:00",
                "status": "repaid",
                "is_eligible": False,
                "employer_id": "EMP-1",
                "employer_name": "Employer",
                "employee_id": "USER-1",
                "user_state": "TX",
                "total_principal_amount": 1000,
                "outstanding_principal_amount": 0,
                "repaid_principal_amount": 1000,
                "total_fee_amount": 10,
                "outstanding_fee_amount": 0,
                "receivable_currency": "USD",
                "days_past_due": 0,
                "amount": 1000,
            }
        ]
    )

    result = PayearlyCalculator(Decimal("3.0")).calculate(portfolio)

    assert result.included_assets == []
    assert result.excluded_assets[0].external_id == "PAY-1"
    assert result.excluded_assets[0].reasons == [
        "status mismatch: expected performing",
        "ineligible flag",
        "outstanding_principal_amount must be > 0",
    ]
