from functools import partial

from anyio.to_thread import run_sync
from loguru import logger

from business.calculator.resolver import CalculatorResolver
from business.enums import FacilityType
from core.clients.covenant_registry import CovenantRegistryClient
from core.exceptions import CalculatorExecutionError
from schemas.covenant import CovenantPublishedResult, CovenantResult, OnChainCovenantResult


class CovenantHandler:
    """Coordinate payload dispatch and covenant execution."""

    def __init__(
        self,
        resolver: CalculatorResolver,
        registry_client: CovenantRegistryClient | None = None,
    ) -> None:
        """Store the resolver used to validate facility calculator inputs.

        Args:
            resolver: Resolver that validates payloads and selects calculators.
            registry_client: Optional smart contract client for publication and reads.
        """

        self._resolver = resolver
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

        resolved = self._resolver.resolve(
            facility_type=facility_type,
            payload=payload,
        )

        try:
            logger.info(
                "Starting covenant calculation for {facility_type}",
                facility_type=facility_type.value,
            )
            result = resolved.calculator.calculate(resolved.portfolio)
            logger.info(
                "Finished covenant calculation for {facility_type}",
                facility_type=facility_type.value,
            )
            return result
        except Exception as exc:  # pragma: no cover - defensive boundary
            msg = "Calculator execution failed"
            raise CalculatorExecutionError(
                details=[{"facility_type": facility_type.value}],
                private_details=[{"facility_type": facility_type.value, "error": str(exc)}],
                message=msg,
            ) from exc

    async def publish(
        self,
        *,
        facility_type: FacilityType,
        result: CovenantResult,
    ) -> CovenantPublishedResult:
        """Publish a calculated covenant result on-chain.

        Args:
            facility_type: Declared facility type for the calculated result.
            result: Covenant result to publish.

        Raises:
            CalculatorExecutionError: If the registry client is not configured.

        Returns:
            CovenantPublishedResult: Covenant result with publication metadata.
        """

        if self._registry_client is None:  # pragma: no cover - dependency guard
            msg = "Covenant registry client is not configured"
            raise CalculatorExecutionError(
                details=[{"facility_type": facility_type.value}],
                message=msg,
            )

        logger.info(
            "Starting covenant publication for {facility_type}",
            facility_type=facility_type.value,
        )
        publication = await self._registry_client.publish_facility_report(
            facility_type=facility_type,
            result=result,
        )
        logger.info(
            "Finished covenant publication for {facility_type} with transaction {transaction_hash}",
            facility_type=facility_type.value,
            transaction_hash=publication.transaction_hash,
        )
        return CovenantPublishedResult(
            **result.model_dump(),
            publication=publication,
        )

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

        calculate = partial(
            self.calculate,
            facility_type=facility_type,
            payload=payload,
        )
        result = await run_sync(calculate)
        return await self.publish(
            facility_type=facility_type,
            result=result,
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
        logger.info(
            "Reading published covenant result for {facility_type}",
            facility_type=facility_type.value,
        )
        return await self._registry_client.get_facility_report(facility_type=facility_type)
