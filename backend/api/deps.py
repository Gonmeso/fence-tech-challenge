from fastapi import Header

from business.calculator.dispatcher import CalculatorDispatcher
from business.covenant import CovenantHandler
from business.enums import FacilityType
from core.clients.covenant_registry import (
    CovenantRegistryClient,
    get_covenant_registry_client,
)
from core.exceptions import InvalidFacilityHeaderError, MissingFacilityHeaderError
from core.settings import get_settings


def get_facility_type_header(
    x_fence_facility_type: str | None = Header(default=None),
) -> FacilityType:
    """Parse and validate the facility type header.

    Args:
        x_fence_facility_type: Raw facility header value from the request.

    Raises:
        MissingFacilityHeaderError: If the header is not provided.
        InvalidFacilityHeaderError: If the header does not map to a facility.

    Returns:
        FacilityType: Parsed facility enum value.
    """

    if x_fence_facility_type is None:
        raise MissingFacilityHeaderError()

    try:
        return FacilityType(x_fence_facility_type)
    except ValueError as exc:
        raise InvalidFacilityHeaderError(
            provided_value=x_fence_facility_type,
        ) from exc


def get_calculator_dispatcher() -> CalculatorDispatcher:
    """Build a calculator dispatcher with the current settings.

    Returns:
        CalculatorDispatcher: Dispatcher configured with current thresholds.
    """

    return CalculatorDispatcher(get_settings())


def get_registry_client() -> CovenantRegistryClient:
    """Build the smart contract registry client for the configured chain.

    Returns:
        CovenantRegistryClient: Chain-aware registry client.
    """

    return get_covenant_registry_client(get_settings())


def get_covenant_handler() -> CovenantHandler:
    """Build the covenant handler used by calculation endpoints.

    Returns:
        CovenantHandler: Handler wired with a calculator dispatcher.
    """

    return CovenantHandler(
        dispatcher=get_calculator_dispatcher(),
        registry_client=get_registry_client(),
    )
