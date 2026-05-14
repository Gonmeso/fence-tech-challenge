from decimal import Decimal

from business.calculator.base import BaseCalculator
from schemas.covenant import CovenantResult
from schemas.educa import EducaPortfolio


class EducaCalculator(BaseCalculator[EducaPortfolio]):
    def calculate(self, portfolio: EducaPortfolio) -> CovenantResult:
        assets = portfolio.assets
        included_assets = [asset for asset in assets if asset.is_eligible()]
        numerator = sum(
            asset.outstanding_amount * asset.interest_rate_percentage
            for asset in included_assets
            if asset.interest_rate_percentage is not None
        )
        denominator = sum(asset.outstanding_amount for asset in included_assets)
        computed_rate = numerator / denominator if denominator else Decimal("0")

        return self._build_result(
            assets=assets,
            included_assets=included_assets,
            computed_rate=computed_rate,
        )
