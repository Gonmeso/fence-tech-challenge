from contextlib import contextmanager

from pydantic import ValidationError

from schemas.nomina import NominaAsset, NominaPortfolio


def build_nomina_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    payload.update(overrides)
    return payload


def test_nomina_asset_is_eligible_for_expected_values() -> None:
    asset = NominaAsset.model_validate(build_nomina_payload())

    assert asset.is_eligible() is True
    assert asset.repayment_months() == 8


def test_nomina_asset_is_case_insensitive_for_status() -> None:
    asset = NominaAsset.model_validate(build_nomina_payload(status="ACTIVE"))

    assert asset.is_eligible() is True


def test_nomina_asset_collects_exclusion_reasons() -> None:
    asset = NominaAsset.model_validate(
        build_nomina_payload(status="settled", is_eligible=False, outstanding_amount=0)
    )

    assert asset.get_exclusion_reasons() == [
        "status mismatch: expected active",
        "ineligible flag",
        "outstanding_amount must be > 0",
    ]


def test_nomina_asset_rejects_invalid_maturity_date_format() -> None:
    with raises_validation_error("maturity_date"):
        NominaAsset.model_validate(build_nomina_payload(maturity_date="2025-01-31"))


def test_nomina_asset_flags_invalid_repayment_months() -> None:
    asset = NominaAsset.model_validate(
        build_nomina_payload(origination_date="2025-01-31", maturity_date="31/01/2025")
    )

    assert asset.is_eligible() is False
    assert asset.get_exclusion_reasons() == ["invalid repayment_months"]


def test_nomina_portfolio_wraps_assets() -> None:
    portfolio = NominaPortfolio.model_validate(
        [build_nomina_payload(), build_nomina_payload(external_id="NOM-2")]
    )

    assert len(portfolio.assets) == 2


@contextmanager
def raises_validation_error(field_name: str):
    try:
        yield
    except ValidationError as exc:
        assert field_name in str(exc)
    else:
        msg = f"Expected ValidationError containing {field_name}"
        raise AssertionError(msg)
