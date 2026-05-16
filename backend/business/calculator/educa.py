from decimal import Decimal

from loguru import logger

from business.calculator.base import BaseCalculator
from schemas.covenant import CovenantResult
from schemas.educa import EducaPortfolio


class EducaCalculator(BaseCalculator[EducaPortfolio]):
    """Calculate the effective rate for Educa portfolios."""

    def calculate(self, portfolio: EducaPortfolio) -> CovenantResult:
        """Calculate the weighted average interest rate for eligible assets.

        Args:
            portfolio: Validated Educa portfolio.

        Returns:
            CovenantResult: Covenant output for the Educa portfolio.
        """

        assets = portfolio.assets
        included_assets = [asset for asset in assets if asset.is_eligible()]
        # Educa already carries a direct interest rate per asset, so the
        # facility covenant is a weighted average by outstanding amount.
        numerator = sum(
            asset.outstanding_amount * asset.interest_rate_percentage
            for asset in included_assets
            if asset.interest_rate_percentage is not None
        )
        denominator = sum(asset.outstanding_amount for asset in included_assets)
        computed_rate = numerator / denominator if denominator else Decimal("0")
        logger.debug(
            "Educa effective rate inputs: total_assets={total_assets}, "
            "included_assets={included_assets}, numerator={numerator}, denominator={denominator}, "
            "computed_rate={computed_rate}",
            total_assets=len(assets),
            included_assets=len(included_assets),
            numerator=str(numerator),
            denominator=str(denominator),
            computed_rate=str(computed_rate),
        )

        return self._build_result(
            assets=assets,
            included_assets=included_assets,
            computed_rate=computed_rate,
        )
