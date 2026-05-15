from abc import ABC, abstractmethod
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BaseFacilityAsset(BaseModel, ABC):
    """Base fields shared across all facility asset payloads."""

    external_id: str
    status: str
    eligible_flag: bool = Field(alias="is_eligible")
    days_past_due: int
    amount: Decimal

    model_config = ConfigDict(populate_by_name=True)

    def is_eligible(self) -> bool:
        """Return whether the asset passes facility-specific exclusion rules.

        Returns:
            bool: ``True`` when the asset has no exclusion reasons.
        """

        return not self.get_exclusion_reasons()

    @abstractmethod
    def get_exclusion_reasons(self) -> list[str]:
        """Return the facility-specific reasons this asset is excluded."""
