from typing import Any

from business.enums import FacilityType


class FenceAppError(Exception):
    """Base application error with a stable API-facing shape."""

    code = "fence_app_error"
    message = "Application error"

    def __init__(self, *, message: str | None = None, details: list[Any] | None = None) -> None:
        """Initialize the error payload.

        Args:
            message: Optional override for the default message.
            details: Optional structured details for clients and logs.

        Returns:
            None: Initializes the exception instance.
        """

        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or []


class MissingFacilityHeaderError(FenceAppError):
    """Raised when the facility type header is absent."""

    code = "missing_facility_header"
    message = "Missing X-Fence-Facility-Type header"


class InvalidFacilityHeaderError(FenceAppError):
    """Raised when the facility type header cannot be parsed."""

    code = "invalid_facility_header"
    message = "Invalid X-Fence-Facility-Type header"

    def __init__(self, *, provided_value: str | None) -> None:
        """Capture the invalid header value for debugging.

        Args:
            provided_value: Raw header value received from the client.

        Returns:
            None: Initializes the exception instance.
        """

        super().__init__(
            details=[
                {
                    "provided_value": provided_value,
                    "allowed_values": [facility_type.value for facility_type in FacilityType],
                }
            ]
        )


class InvalidJsonPayloadError(FenceAppError):
    """Raised when the request body is not valid JSON."""

    code = "invalid_json_payload"
    message = "Payload is not valid JSON"


class InvalidPayloadTypeError(FenceAppError):
    """Raised when the request body is not a JSON array."""

    code = "invalid_payload_type"
    message = "Payload must be a JSON array of assets"


class FacilityPayloadValidationError(FenceAppError):
    """Raised when the payload does not match the declared facility schema."""

    code = "facility_payload_validation_error"
    message = "Payload does not match the declared facility schema"

    def __init__(self, *, facility_type: FacilityType, details: list[Any]) -> None:
        """Attach validation details for the declared facility.

        Args:
            facility_type: Facility declared by the caller.
            details: Pydantic validation errors produced for the payload.

        Returns:
            None: Initializes the exception instance.
        """

        super().__init__(
            details=[
                {
                    "facility_type": facility_type.value,
                    "validation_errors": details,
                }
            ]
        )


class UnsupportedFacilityError(FenceAppError):
    """Raised when a facility is not implemented."""

    code = "unsupported_facility"
    message = "Unsupported facility type"


class CalculatorExecutionError(FenceAppError):
    """Raised when calculator execution fails after successful validation."""

    code = "calculator_execution_error"
    message = "Failed to calculate covenant result"


class CovenantRegistryConfigurationError(FenceAppError):
    """Raised when smart contract settings are incomplete or invalid."""

    code = "covenant_registry_configuration_error"
    message = "Covenant registry configuration is incomplete"


class CovenantPublicationError(FenceAppError):
    """Raised when the covenant report cannot be published on-chain."""

    code = "covenant_publication_error"
    message = "Failed to publish covenant result on-chain"


class CovenantReportNotFoundError(FenceAppError):
    """Raised when no on-chain covenant report exists for the facility."""

    code = "covenant_report_not_found"
    message = "No covenant result has been published for this facility"

    def __init__(self, *, facility_type: FacilityType) -> None:
        """Capture the facility that does not have an on-chain report.

        Args:
            facility_type: Facility requested by the caller.

        Returns:
            None: Initializes the exception instance.
        """

        super().__init__(details=[{"facility_type": facility_type.value}])


class CovenantRegistryReadError(FenceAppError):
    """Raised when the covenant report cannot be read from the contract."""

    code = "covenant_registry_read_error"
    message = "Failed to read covenant result from the smart contract"
