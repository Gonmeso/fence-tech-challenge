import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from business.calculator.base import BaseCalculator
from business.calculator.educa import EducaCalculator
from business.calculator.nomina import NominaCalculator
from business.calculator.payearly import PayearlyCalculator
from business.enums import FacilityType
from core.exceptions import (
    FacilityPayloadValidationError,
    InvalidJsonPayloadError,
    InvalidPayloadTypeError,
    UnsupportedFacilityError,
)
from core.settings import Settings
from schemas.educa import EducaPortfolio
from schemas.nomina import NominaPortfolio
from schemas.payearly import PayearlyPortfolio


@dataclass(frozen=True)
class DispatchedCalculator:
    facility_type: FacilityType
    portfolio: EducaPortfolio | PayearlyPortfolio | NominaPortfolio
    calculator: BaseCalculator[Any]


class CalculatorDispatcher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def dispatch(
        self,
        *,
        facility_type: FacilityType,
        payload: str | bytes | list[dict[str, Any]],
    ) -> DispatchedCalculator:
        parsed_payload = self._parse_payload(payload)

        portfolio_schema: type[EducaPortfolio | PayearlyPortfolio | NominaPortfolio]
        calculator: BaseCalculator[Any]

        if facility_type is FacilityType.EDUCA:
            portfolio_schema = EducaPortfolio
            calculator = EducaCalculator(self._settings.educa_covenant_threshold)
        elif facility_type is FacilityType.PAYEARLY:
            portfolio_schema = PayearlyPortfolio
            calculator = PayearlyCalculator(self._settings.payearly_covenant_threshold)
        elif facility_type is FacilityType.NOMINA:
            portfolio_schema = NominaPortfolio
            calculator = NominaCalculator(self._settings.nomina_covenant_threshold)
        else:  # pragma: no cover - defensive boundary
            raise UnsupportedFacilityError(
                details=[{"facility_type": str(facility_type)}],
            )

        try:
            portfolio = portfolio_schema.model_validate(parsed_payload)
        except ValidationError as exc:
            raise FacilityPayloadValidationError(
                facility_type=facility_type,
                details=exc.errors(),
            ) from exc

        return DispatchedCalculator(
            facility_type=facility_type,
            portfolio=portfolio,
            calculator=calculator,
        )

    @staticmethod
    def _parse_payload(payload: str | bytes | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, bytes):
            payload = payload.decode()

        try:
            parsed_payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise InvalidJsonPayloadError() from exc

        if not isinstance(parsed_payload, list):
            raise InvalidPayloadTypeError()

        return parsed_payload
