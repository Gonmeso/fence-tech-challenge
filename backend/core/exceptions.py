from typing import Any

from business.enums import FacilityType


class FenceAppError(Exception):
    code = "fence_app_error"
    message = "Application error"

    def __init__(self, *, message: str | None = None, details: list[Any] | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or []


class MissingFacilityHeaderError(FenceAppError):
    code = "missing_facility_header"
    message = "Missing X-Fence-Facility-Type header"


class InvalidFacilityHeaderError(FenceAppError):
    code = "invalid_facility_header"
    message = "Invalid X-Fence-Facility-Type header"

    def __init__(self, *, provided_value: str | None) -> None:
        super().__init__(
            details=[
                {
                    "provided_value": provided_value,
                }
            ]
        )


class InvalidJsonPayloadError(FenceAppError):
    code = "invalid_json_payload"
    message = "Payload is not valid JSON"


class InvalidPayloadTypeError(FenceAppError):
    code = "invalid_payload_type"
    message = "Payload must be a JSON array of assets"


class FacilityPayloadValidationError(FenceAppError):
    code = "facility_payload_validation_error"
    message = "Payload does not match the declared facility schema"

    def __init__(self, *, facility_type: FacilityType, details: list[Any]) -> None:
        super().__init__(
            details=[
                {
                    "facility_type": facility_type.value,
                    "validation_errors": details,
                }
            ]
        )


class UnsupportedFacilityError(FenceAppError):
    code = "unsupported_facility"
    message = "Unsupported facility type"


class CalculatorExecutionError(FenceAppError):
    code = "calculator_execution_error"
    message = "Failed to calculate covenant result"
