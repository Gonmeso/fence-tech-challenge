from datetime import date, datetime
from decimal import Decimal

from pydantic import RootModel

from schemas.base import BaseFacilityAsset


class PayearlyAsset(BaseFacilityAsset):
    """One Payearly asset row as provided by the source data."""

    created_at: datetime
    due_date: date
    last_updated: datetime
    employer_id: str
    employer_name: str
    employee_id: str
    user_state: str
    total_principal_amount: Decimal
    outstanding_principal_amount: Decimal
    repaid_principal_amount: Decimal
    total_fee_amount: Decimal
    outstanding_fee_amount: Decimal
    receivable_currency: str

    def tenor_days(self) -> int:
        """Return the asset tenor in days.

        Returns:
            int: Number of days between creation and due date.
        """

        return (self.due_date - self.created_at.date()).days

    def get_exclusion_reasons(self) -> list[str]:
        """Return all Payearly-specific reasons the asset is excluded.

        Returns:
            list[str]: Exclusion reasons collected for the asset.
        """

        reasons: list[str] = []

        if self.status.casefold() != "performing":
            reasons.append("status mismatch: expected performing")
        if not self.eligible_flag:
            reasons.append("ineligible flag")
        if self.outstanding_principal_amount <= 0:
            reasons.append("outstanding_principal_amount must be > 0")
        if self.total_principal_amount <= 0:
            reasons.append("total_principal_amount must be > 0")
        if self.tenor_days() <= 0:
            reasons.append("invalid tenor_days")

        return reasons


class PayearlyPortfolio(RootModel[list[PayearlyAsset]]):
    """Wrapper used to validate lists of Payearly assets."""

    @property
    def assets(self) -> list[PayearlyAsset]:
        """Expose the wrapped asset list with a stable name.

        Returns:
            list[PayearlyAsset]: Validated Payearly assets.
        """

        return self.root
