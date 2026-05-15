from fastapi import Header

from business.calculator.dispatcher import CalculatorDispatcher
from business.covenant import CovenantHandler
from business.enums import FacilityType
from core.exceptions import InvalidFacilityHeaderError, MissingFacilityHeaderError
from core.settings import get_settings


def get_facility_type_header(
    x_fence_facility_type: str | None = Header(default=None),
) -> FacilityType:
    if x_fence_facility_type is None:
        raise MissingFacilityHeaderError()

    try:
        return FacilityType(x_fence_facility_type)
    except ValueError as exc:
        raise InvalidFacilityHeaderError(
            provided_value=x_fence_facility_type,
        ) from exc


def get_calculator_dispatcher() -> CalculatorDispatcher:
    return CalculatorDispatcher(get_settings())


def get_covenant_handler() -> CovenantHandler:
    return CovenantHandler(get_calculator_dispatcher())
