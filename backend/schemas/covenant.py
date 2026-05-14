from enum import StrEnum

from pydantic import BaseModel


class CovenantStatus(StrEnum):
    COMPLIANT = "COMPLIANT"
    BREACH = "BREACH"


class ExcludedAsset(BaseModel):
    external_id: str
    reasons: list[str]


class CovenantSummary(BaseModel):
    total_assets_evaluated: int
    assets_included: int
    assets_excluded: int


class CovenantResult(BaseModel):
    computed_effective_rate: float
    covenant_status: CovenantStatus
    summary: CovenantSummary
    included_assets: list[str]
    excluded_assets: list[ExcludedAsset]
