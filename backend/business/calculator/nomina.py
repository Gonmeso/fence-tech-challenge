from decimal import Decimal

from loguru import logger

from business.calculator.base import BaseCalculator
from schemas.covenant import CovenantResult
from schemas.nomina import NominaPortfolio


class NominaCalculator(BaseCalculator[NominaPortfolio]):
    """Calculate the annualized effective rate for Nomina portfolios."""

    def calculate(self, portfolio: NominaPortfolio) -> CovenantResult:
        """Calculate the weighted average annualized fee rate.

        Args:
            portfolio: Validated Nomina portfolio.

        Returns:
            CovenantResult: Covenant output for the Nomina portfolio.
        """

        assets = portfolio.assets
        included_assets = [asset for asset in assets if asset.is_eligible()]
        # Nomina expresses fee as a periodic percentage, so the covenant rate
        # annualizes it by repayment duration and weights by exposure.
        numerator = sum(
            asset.outstanding_amount
            * (asset.fee_percentage * (Decimal("12") / asset.repayment_months()))
            for asset in included_assets
        )
        denominator = sum(asset.outstanding_amount for asset in included_assets)
        computed_rate = numerator / denominator if denominator else Decimal("0")
        logger.debug(
            "Nomina effective rate inputs: total_assets={total_assets}, "
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
