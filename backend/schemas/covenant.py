from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, field_serializer


class CovenantStatus(StrEnum):
    """Possible covenant outcomes."""

    COMPLIANT = "COMPLIANT"
    BREACH = "BREACH"


class ExcludedAsset(BaseModel):
    """Asset omitted from the calculation with its exclusion reasons."""

    external_id: str
    reasons: list[str]


class CovenantSummary(BaseModel):
    """High-level counts for evaluated, included, and excluded assets."""

    total_assets_evaluated: int
    assets_included: int
    assets_excluded: int


class CovenantResult(BaseModel):
    """Final covenant output returned by calculators and the API."""

    computed_effective_rate: Decimal
    covenant_status: CovenantStatus
    summary: CovenantSummary
    included_assets: list[str]
    excluded_assets: list[ExcludedAsset]

    @field_serializer("computed_effective_rate", when_used="json")
    def serialize_computed_effective_rate(self, value: Decimal) -> str:
        """Serialize rates as strings to preserve decimal precision.

        Args:
            value: Decimal effective rate.

        Returns:
            str: Decimal rate formatted for JSON responses.
        """

        return str(value)


class CovenantPublication(BaseModel):
    """Metadata for a covenant report published on-chain."""

    chain_id: int
    contract_address: str
    transaction_hash: str


class CovenantPublishedResult(CovenantResult):
    """Covenant calculation response with publication metadata."""

    publication: CovenantPublication


class OnChainCovenantResult(BaseModel):
    """Latest covenant report read from the smart contract."""

    facility: str
    effective_rate_bps: int
    computed_effective_rate: Decimal
    covenant_status: CovenantStatus
    summary: CovenantSummary
    included_assets: list[str]
    excluded_assets: list[str]
    updated_at: int
    exists: bool
    chain_id: int
    contract_address: str

    @field_serializer("computed_effective_rate", when_used="json")
    def serialize_computed_effective_rate(self, value: Decimal) -> str:
        """Serialize rates as strings to preserve decimal precision.

        Args:
            value: Decimal effective rate.

        Returns:
            str: Decimal rate formatted for JSON responses.
        """

        return str(value)
