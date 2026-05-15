from enum import StrEnum

from pydantic import BaseModel


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

    computed_effective_rate: float
    covenant_status: CovenantStatus
    summary: CovenantSummary
    included_assets: list[str]
    excluded_assets: list[ExcludedAsset]
