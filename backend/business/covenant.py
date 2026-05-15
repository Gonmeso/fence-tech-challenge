from business.calculator.dispatcher import CalculatorDispatcher
from business.enums import FacilityType
from core.exceptions import CalculatorExecutionError
from schemas.covenant import CovenantResult


class CovenantHandler:
    def __init__(self, dispatcher: CalculatorDispatcher) -> None:
        self._dispatcher = dispatcher

    def calculate(
        self,
        *,
        facility_type: FacilityType,
        payload: str | bytes | list[dict[str, object]],
    ) -> CovenantResult:
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
