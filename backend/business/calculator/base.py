from abc import ABC, abstractmethod
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from loguru import logger

from schemas.base import BaseFacilityAsset
from schemas.covenant import (
    CovenantResult,
    CovenantStatus,
    CovenantSummary,
    ExcludedAsset,
)


class BaseCalculator[PortfolioT](ABC):
    """Base class for facility covenant calculators."""

    def __init__(self, threshold: Decimal) -> None:
        """Store the covenant threshold used for compliance checks.

        Args:
            threshold: Maximum compliant effective rate for the facility.
        """

        self.threshold = threshold

    @abstractmethod
    def calculate(self, portfolio: PortfolioT) -> CovenantResult:
        """Calculate the facility covenant result.

        Args:
            portfolio: Validated facility portfolio to evaluate.

        Returns:
            CovenantResult: Facility-specific covenant output.
        """

    def _round_rate(self, value: Decimal) -> Decimal:
        """Round rates to the two-decimal API representation.

        Args:
            value: Effective rate before serialization.

        Returns:
            Decimal: Rounded rate ready for the response payload.
        """

        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _build_result(
        self,
        *,
        assets: Sequence[BaseFacilityAsset],
        included_assets: Sequence[BaseFacilityAsset],
        computed_rate: Decimal,
    ) -> CovenantResult:
        """Build the common response payload for all facilities.

        Args:
            assets: All assets received for evaluation.
            included_assets: Eligible assets included in the calculation.
            computed_rate: Effective rate computed by the facility calculator.

        Returns:
            CovenantResult: Standardized covenant response.
        """

        excluded_assets = [
            ExcludedAsset(
                external_id=asset.external_id,
                reasons=asset.get_exclusion_reasons(),
            )
            for asset in assets
            if not asset.is_eligible()
        ]
        covenant_status = (
            CovenantStatus.COMPLIANT if computed_rate < self.threshold else CovenantStatus.BREACH
        )
        logger.debug(
            "Built covenant result with {included_assets}/{total_assets} included assets, "
            "computed rate {computed_rate}, threshold {threshold}, status {status}",
            included_assets=len(included_assets),
            total_assets=len(assets),
            computed_rate=str(computed_rate),
            threshold=str(self.threshold),
            status=covenant_status.value,
        )

        return CovenantResult(
            computed_effective_rate=self._round_rate(computed_rate),
            covenant_status=covenant_status,
            summary=CovenantSummary(
                total_assets_evaluated=len(assets),
                assets_included=len(included_assets),
                assets_excluded=len(excluded_assets),
            ),
            included_assets=[asset.external_id for asset in included_assets],
            excluded_assets=excluded_assets,
        )
