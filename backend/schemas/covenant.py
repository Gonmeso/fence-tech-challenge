from decimal import Decimal
from enum import StrEnum
from typing import Any, cast

from pydantic import BaseModel, field_serializer, model_validator


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
    excluded_assets: list[ExcludedAsset]
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


class ContractExcludedAsset(BaseModel):
    """Excluded asset entry returned by the smart contract."""

    external_id: str
    reasons: list[str]

    @model_validator(mode="before")
    @classmethod
    def from_contract_tuple(cls, data: object) -> object:
        """Support web3 tuple results as model input."""

        if isinstance(data, (list, tuple)):
            tuple_data = cast(tuple[Any, ...], data)
            if len(tuple_data) != 2:
                raise ValueError("Excluded asset contract tuple must contain 2 items")
            reasons = tuple_data[1]
            if not isinstance(reasons, (list, tuple)):
                raise ValueError("Excluded asset reasons must be a list or tuple")
            return {
                "external_id": str(tuple_data[0]),
                "reasons": [str(reason) for reason in reasons],
            }
        return data


class ContractFacilityReport(BaseModel):
    """Validated smart contract report shape returned by web3."""

    facility: str
    effective_rate_bps: int
    covenant_status: int
    total_assets_evaluated: int
    assets_included_count: int
    assets_excluded_count: int
    included_external_ids: list[str]
    excluded_assets: list[ContractExcludedAsset]
    updated_at: int
    updated_by: str
    exists: bool

    @model_validator(mode="before")
    @classmethod
    def from_contract_tuple(cls, data: object) -> object:
        """Support web3 tuple results as model input."""

        if isinstance(data, (list, tuple)):
            tuple_data = cast(tuple[Any, ...], data)
            if len(tuple_data) != 11:
                raise ValueError("Facility report contract tuple must contain 11 items")
            included_external_ids = tuple_data[6]
            excluded_assets = tuple_data[7]
            if not isinstance(included_external_ids, (list, tuple)):
                raise ValueError("Included external IDs must be a list or tuple")
            if not isinstance(excluded_assets, (list, tuple)):
                raise ValueError("Excluded assets must be a list or tuple")
            return {
                "facility": str(tuple_data[0]),
                "effective_rate_bps": int(tuple_data[1]),
                "covenant_status": int(tuple_data[2]),
                "total_assets_evaluated": int(tuple_data[3]),
                "assets_included_count": int(tuple_data[4]),
                "assets_excluded_count": int(tuple_data[5]),
                "included_external_ids": [
                    str(external_id) for external_id in included_external_ids
                ],
                "excluded_assets": list(excluded_assets),
                "updated_at": int(tuple_data[8]),
                "updated_by": str(tuple_data[9]),
                "exists": bool(tuple_data[10]),
            }
        return data

    @model_validator(mode="after")
    def validate_summary_consistency(self) -> "ContractFacilityReport":
        """Reject malformed contract data with inconsistent counts."""

        if self.assets_included_count != len(self.included_external_ids):
            raise ValueError("Included asset count does not match included asset list length")
        if self.assets_excluded_count != len(self.excluded_assets):
            raise ValueError("Excluded asset count does not match excluded asset list length")
        if self.total_assets_evaluated != self.assets_included_count + self.assets_excluded_count:
            raise ValueError("Total assets evaluated does not match included plus excluded counts")
        return self
