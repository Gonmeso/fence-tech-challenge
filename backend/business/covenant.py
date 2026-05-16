from business.calculator.dispatcher import CalculatorDispatcher
from business.enums import FacilityType
from core.clients.covenant_registry import CovenantRegistryClient
from core.exceptions import CalculatorExecutionError
from schemas.covenant import CovenantPublishedResult, CovenantResult, OnChainCovenantResult


class CovenantHandler:
    """Coordinate payload dispatch and covenant execution."""

    def __init__(
        self,
        dispatcher: CalculatorDispatcher,
        registry_client: CovenantRegistryClient | None = None,
    ) -> None:
        """Store the dispatcher used to resolve facility calculators.

        Args:
            dispatcher: Dispatcher that validates payloads and selects calculators.
            registry_client: Optional smart contract client for publication and reads.
        """

        self._dispatcher = dispatcher
        self._registry_client = registry_client

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

    async def calculate_and_publish(
        self,
        *,
        facility_type: FacilityType,
        payload: str | bytes | list[dict[str, object]],
    ) -> CovenantPublishedResult:
        """Calculate the covenant result and publish it on-chain.

        Args:
            facility_type: Declared facility type for the incoming payload.
            payload: Raw JSON string, raw bytes, or pre-parsed asset list.

        Raises:
            CalculatorExecutionError: If calculator execution fails unexpectedly.

        Returns:
            CovenantPublishedResult: Covenant result with publication metadata.
        """

        # If the payload were big, this should run in a threadpool to avoid blocking the event loop.
        # For simplicity, we assume it's small enough to not require that.
        result = self.calculate(facility_type=facility_type, payload=payload)
        if self._registry_client is None:  # pragma: no cover - dependency guard
            msg = "Covenant registry client is not configured"
            raise CalculatorExecutionError(
                details=[{"facility_type": facility_type.value}],
                message=msg,
            )

        publication = await self._registry_client.publish_facility_report(
            facility_type=facility_type,
            result=result,
        )
        return CovenantPublishedResult(
            **result.model_dump(),
            publication=publication,
        )

    async def get_published_result(
        self,
        *,
        facility_type: FacilityType,
    ) -> OnChainCovenantResult:
        """Read the latest on-chain covenant result for a facility.

        Args:
            facility_type: Facility declared by the caller.

        Returns:
            OnChainCovenantResult: Latest report stored in the registry.
        """

        if self._registry_client is None:  # pragma: no cover - dependency guard
            msg = "Covenant registry client is not configured"
            raise CalculatorExecutionError(
                details=[{"facility_type": facility_type.value}],
                message=msg,
            )
        return await self._registry_client.get_facility_report(facility_type=facility_type)
