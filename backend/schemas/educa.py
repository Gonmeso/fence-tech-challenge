from datetime import date
from decimal import Decimal

from pydantic import RootModel

from schemas.base import BaseFacilityAsset


class EducaAsset(BaseFacilityAsset):
    """One Educa asset row as provided by the source data."""

    effective_date: date
    reporting_date: date
    student_id: str
    school_id: str
    loan_status: str
    disbursement_amount: Decimal
    outstanding_amount: Decimal
    repaid_amount: Decimal
    interest_rate_percentage: Decimal | None
    country: str

    def get_exclusion_reasons(self) -> list[str]:
        """Return all Educa-specific reasons the asset is excluded.

        Returns:
            list[str]: Exclusion reasons collected for the asset.
        """

        reasons: list[str] = []

        if self.status.casefold() != "open":
            reasons.append("status mismatch: expected open")
        if not self.eligible_flag:
            reasons.append("ineligible flag")
        if self.loan_status.casefold() != "current":
            reasons.append("loan_status mismatch: expected current")
        if self.interest_rate_percentage is None:
            reasons.append("missing interest_rate_percentage")

        return reasons


class EducaPortfolio(RootModel[list[EducaAsset]]):
    """Wrapper used to validate lists of Educa assets."""

    @property
    def assets(self) -> list[EducaAsset]:
        """Expose the wrapped asset list with a stable name.

        Returns:
            list[EducaAsset]: Validated Educa assets.
        """

        return self.root
