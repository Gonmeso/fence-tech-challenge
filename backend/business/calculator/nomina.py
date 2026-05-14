from decimal import Decimal

from business.calculator.base import BaseCalculator
from schemas.covenant import CovenantResult
from schemas.nomina import NominaPortfolio


class NominaCalculator(BaseCalculator[NominaPortfolio]):
    def calculate(self, portfolio: NominaPortfolio) -> CovenantResult:
        assets = portfolio.assets
        included_assets = [asset for asset in assets if asset.is_eligible()]
        numerator = sum(
            asset.outstanding_amount
            * (asset.fee_percentage * (Decimal("12") / asset.repayment_months()))
            for asset in included_assets
        )
        denominator = sum(asset.outstanding_amount for asset in included_assets)
        computed_rate = numerator / denominator if denominator else Decimal("0")

        return self._build_result(
            assets=assets,
            included_assets=included_assets,
            computed_rate=computed_rate,
        )
