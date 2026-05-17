import json
from decimal import Decimal
from pathlib import Path

from business.calculator import EducaCalculator, NominaCalculator, PayearlyCalculator
from core.settings import Settings
from schemas.covenant import CovenantStatus
from schemas.educa import EducaPortfolio
from schemas.nomina import NominaPortfolio
from schemas.payearly import PayearlyPortfolio


def load_json(path: Path) -> str:
    return json.dumps(json.loads(path.read_text()))


def test_educa_calculator_with_real_json(data_dir: Path, settings: Settings) -> None:
    portfolio = EducaPortfolio.model_validate_json(
        load_json(data_dir / "facility_a_educa_isa.json")
    )

    result = EducaCalculator(settings.educa_covenant_threshold).calculate(portfolio)

    assert result.computed_effective_rate == Decimal("18.33")
    assert result.covenant_status == CovenantStatus.COMPLIANT
    assert result.summary.total_assets_evaluated == 8
    assert result.summary.assets_included == 5
    assert result.summary.assets_excluded == 3


def test_payearly_calculator_with_real_json(data_dir: Path, settings: Settings) -> None:
    portfolio = PayearlyPortfolio.model_validate_json(
        load_json(data_dir / "facility_b_payearly_ewa.json")
    )

    result = PayearlyCalculator(settings.payearly_covenant_threshold).calculate(portfolio)

    assert result.computed_effective_rate == Decimal("0.03")
    assert result.covenant_status == CovenantStatus.COMPLIANT
    assert result.summary.total_assets_evaluated == 8
    assert result.summary.assets_included == 5
    assert result.summary.assets_excluded == 3


def test_nomina_calculator_with_real_json(data_dir: Path, settings: Settings) -> None:
    portfolio = NominaPortfolio.model_validate_json(load_json(data_dir / "facility_c_nomina.json"))

    result = NominaCalculator(settings.nomina_covenant_threshold).calculate(portfolio)

    assert result.computed_effective_rate == Decimal("3.39")
    assert result.covenant_status == CovenantStatus.COMPLIANT
    assert result.summary.total_assets_evaluated == 8
    assert result.summary.assets_included == 4
    assert result.summary.assets_excluded == 4
