from decimal import Decimal

from business.calculator.base import BaseCalculator
from schemas.covenant import CovenantResult
from schemas.payearly import PayearlyPortfolio


class PayearlyCalculator(BaseCalculator[PayearlyPortfolio]):
    """Calculate the annualized effective rate for Payearly portfolios."""

    def calculate(self, portfolio: PayearlyPortfolio) -> CovenantResult:
        """Calculate the weighted average annualized fee rate.

        Args:
            portfolio: Validated Payearly portfolio.

        Returns:
            CovenantResult: Covenant output for the Payearly portfolio.
        """

        assets = portfolio.assets
        included_assets = [asset for asset in assets if asset.is_eligible()]
        # The challenge defines Payearly's effective rate as fee over principal,
        # annualized by the asset tenor and weighted by outstanding principal.
        numerator = sum(
            asset.outstanding_principal_amount
            * (
                (asset.total_fee_amount / asset.total_principal_amount)
                * (Decimal("365") / asset.tenor_days())
            )
            for asset in included_assets
        )
        denominator = sum(asset.outstanding_principal_amount for asset in included_assets)
        computed_rate = numerator / denominator if denominator else Decimal("0")

        return self._build_result(
            assets=assets,
            included_assets=included_assets,
            computed_rate=computed_rate,
        )
