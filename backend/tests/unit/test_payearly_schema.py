from contextlib import contextmanager

from pydantic import ValidationError

from schemas.payearly import PayearlyAsset, PayearlyPortfolio


def build_payearly_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    payload.update(overrides)
    return payload


def test_payearly_asset_is_eligible_for_expected_values() -> None:
    asset = PayearlyAsset.model_validate(build_payearly_payload())

    assert asset.is_eligible() is True
    assert asset.tenor_days() == 273


def test_payearly_asset_accepts_status_in_different_case() -> None:
    asset = PayearlyAsset.model_validate(build_payearly_payload(status="PERFORMING"))

    assert asset.is_eligible() is True


def test_payearly_asset_collects_exclusion_reasons() -> None:
    asset = PayearlyAsset.model_validate(
        build_payearly_payload(
            status="defaulted",
            is_eligible=False,
            outstanding_principal_amount=0,
        )
    )

    assert asset.get_exclusion_reasons() == [
        "status mismatch: expected performing",
        "ineligible flag",
        "outstanding_principal_amount must be > 0",
    ]


def test_payearly_asset_rejects_invalid_datetime() -> None:
    with raises_validation_error("created_at"):
        PayearlyAsset.model_validate(build_payearly_payload(created_at="not-a-datetime"))


def test_payearly_asset_flags_invalid_tenor() -> None:
    asset = PayearlyAsset.model_validate(
        build_payearly_payload(created_at="2026-03-15T09:00:00+00:00", due_date="2026-03-15")
    )

    assert asset.is_eligible() is False
    assert asset.get_exclusion_reasons() == ["invalid tenor_days"]


def test_payearly_portfolio_wraps_assets() -> None:
    portfolio = PayearlyPortfolio.model_validate(
        [build_payearly_payload(), build_payearly_payload(external_id="PAY-2")]
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
