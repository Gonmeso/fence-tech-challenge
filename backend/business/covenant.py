from business.calculator.dispatcher import CalculatorDispatcher
from business.enums import FacilityType
from core.exceptions import CalculatorExecutionError
from schemas.covenant import CovenantResult


class CovenantHandler:
    """Coordinate payload dispatch and covenant execution."""

    def __init__(self, dispatcher: CalculatorDispatcher) -> None:
        """Store the dispatcher used to resolve facility calculators.

        Args:
            dispatcher: Dispatcher that validates payloads and selects calculators.
        """

        self._dispatcher = dispatcher

    def calculate(
        self,
        *,
        facility_type: FacilityType,
        payload: str | bytes | list[dict[str, object]],
    ) -> CovenantResult:
        """Calculate the covenant result for the declared facility payload.

        Args:
            facility_type: Declared facility type for the incoming payload.
            payload: Raw JSON string, raw bytes, or pre-parsed asset list.

        Raises:
            CalculatorExecutionError: If calculator execution fails unexpectedly.

        Returns:
            CovenantResult: Calculated covenant response.
        """

        dispatched = self._dispatcher.dispatch(
            facility_type=facility_type,
            payload=payload,
        )

        try:
            return dispatched.calculator.calculate(dispatched.portfolio)
        except Exception as exc:  # pragma: no cover - defensive boundary
            msg = "Calculator execution failed"
            raise CalculatorExecutionError(
                details=[{"facility_type": facility_type.value, "error": str(exc)}],
                message=msg,
            ) from exc
