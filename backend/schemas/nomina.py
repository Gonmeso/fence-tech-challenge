from datetime import date, datetime
from decimal import Decimal

from pydantic import RootModel, field_validator

from schemas.base import BaseFacilityAsset


class NominaAsset(BaseFacilityAsset):
    origination_date: date
    cutoff_date: date
    employer_name: str
    employer_tax_id: str
    net_monthly_salary: Decimal
    advance_amount: Decimal
    outstanding_amount: Decimal
    repaid_amount: Decimal
    fee_percentage: Decimal
    fee_amount: Decimal
    maturity_date: date

    @field_validator("maturity_date", mode="before")
    @classmethod
    def parse_maturity_date(cls, value: str | date) -> date:
        if isinstance(value, date):
            return value
        return datetime.strptime(value, "%d/%m/%Y").date()

    def repayment_months(self) -> int:
        return (
            (self.maturity_date.year - self.origination_date.year) * 12
            + self.maturity_date.month
            - self.origination_date.month
        )

    def get_exclusion_reasons(self) -> list[str]:
        reasons: list[str] = []

        if self.status.casefold() != "active":
            reasons.append("status mismatch: expected active")
        if not self.eligible_flag:
            reasons.append("ineligible flag")
        if self.outstanding_amount <= 0:
            reasons.append("outstanding_amount must be > 0")
        if self.repayment_months() <= 0:
            reasons.append("invalid repayment_months")

        return reasons


class NominaPortfolio(RootModel[list[NominaAsset]]):
    @property
    def assets(self) -> list[NominaAsset]:
        return self.root
