from abc import ABC, abstractmethod
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from schemas.base import BaseFacilityAsset
from schemas.covenant import (
    CovenantResult,
    CovenantStatus,
    CovenantSummary,
    ExcludedAsset,
)


class BaseCalculator[PortfolioT](ABC):
    def __init__(self, threshold: Decimal) -> None:
        self.threshold = threshold

    @abstractmethod
    def calculate(self, portfolio: PortfolioT) -> CovenantResult:
        """Calculate the facility covenant result."""

    def _round_rate(self, value: Decimal) -> float:
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def _build_result(
        self,
        *,
        assets: Sequence[BaseFacilityAsset],
        included_assets: Sequence[BaseFacilityAsset],
        computed_rate: Decimal,
    ) -> CovenantResult:
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
