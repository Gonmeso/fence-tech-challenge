from enum import StrEnum


class FacilityType(StrEnum):
    """Supported facility identifiers used in the API and business layer."""

    EDUCA = "educa"
    PAYEARLY = "payearly"
    NOMINA = "nomina"
