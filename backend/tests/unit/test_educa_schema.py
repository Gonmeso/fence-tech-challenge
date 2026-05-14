from contextlib import contextmanager
from decimal import Decimal

from pydantic import ValidationError

from schemas.educa import EducaAsset, EducaPortfolio


def build_educa_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    payload.update(overrides)
    return payload


def test_educa_asset_is_eligible_for_expected_values() -> None:
    asset = EducaAsset.model_validate(build_educa_payload())

    assert asset.is_eligible() is True
    assert asset.get_exclusion_reasons() == []


def test_educa_asset_is_case_insensitive_for_status_and_loan_status() -> None:
    asset = EducaAsset.model_validate(
        build_educa_payload(status="OPEN", loan_status="CURRENT"),
    )

    assert asset.is_eligible() is True


def test_educa_asset_collects_exclusion_reasons() -> None:
    asset = EducaAsset.model_validate(
        build_educa_payload(
            status="closed",
            is_eligible=False,
            loan_status="delinquent",
            interest_rate_percentage=None,
        )
    )

    assert asset.is_eligible() is False
    assert asset.get_exclusion_reasons() == [
        "status mismatch: expected open",
        "ineligible flag",
        "loan_status mismatch: expected current",
        "missing interest_rate_percentage",
    ]


def test_educa_asset_accepts_numeric_strings_for_decimal_fields() -> None:
    asset = EducaAsset.model_validate(
        build_educa_payload(
            amount="6500.0",
            outstanding_amount="4875.0",
            interest_rate_percentage="20.86",
        )
    )

    assert asset.amount == 6500
    assert asset.outstanding_amount == 4875
    assert asset.interest_rate_percentage == Decimal("20.86")


def test_educa_asset_rejects_null_required_values() -> None:
    with pytest_raises_validation_error("status"):
        EducaAsset.model_validate(build_educa_payload(status=None))


def test_educa_asset_rejects_invalid_date_format() -> None:
    with pytest_raises_validation_error("effective_date"):
        EducaAsset.model_validate(build_educa_payload(effective_date="25/06/2024"))


def test_educa_portfolio_wraps_list_of_assets() -> None:
    portfolio = EducaPortfolio.model_validate(
        [build_educa_payload(), build_educa_payload(external_id="EDU-2")]
    )

    assert len(portfolio.assets) == 2
    assert portfolio.assets[1].external_id == "EDU-2"


@contextmanager
def pytest_raises_validation_error(field_name: str):
    try:
        yield
    except ValidationError as exc:
        assert field_name in str(exc)
    else:
        msg = f"Expected ValidationError containing {field_name}"
        raise AssertionError(msg)
