from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol

from eth_account import Account
from loguru import logger
from web3 import AsyncHTTPProvider, AsyncWeb3

from business.enums import FacilityType
from core.exceptions import (
    CovenantPublicationError,
    CovenantRegistryConfigurationError,
    CovenantRegistryReadError,
    CovenantReportNotFoundError,
)
from core.settings import Settings
from core.utils.contract_abi import load_registry_abi
from schemas.covenant import (
    CovenantPublication,
    CovenantResult,
    CovenantStatus,
    CovenantSummary,
    OnChainCovenantResult,
)


class CovenantRegistryClient(Protocol):
    """Interface used by business code to interact with the registry."""

    chain_id: int
    contract_address: str

    async def publish_facility_report(
        self,
        *,
        facility_type: FacilityType,
        result: CovenantResult,
    ) -> CovenantPublication:
        """Publish a calculated covenant result on-chain.

        Args:
            facility_type: Facility associated with the covenant result.
            result: Calculated covenant output.

        Raises:
            CovenantPublicationError: If the transaction fails.

        Returns:
            CovenantPublication: Transaction metadata for the publication.
        """

    async def get_facility_report(self, *, facility_type: FacilityType) -> OnChainCovenantResult:
        """Read the latest published covenant report for a facility.

        Args:
            facility_type: Facility to read from the registry.

        Raises:
            CovenantReportNotFoundError: If no report exists for the facility.
            CovenantRegistryReadError: If the contract read fails.

        Returns:
            OnChainCovenantResult: Latest report stored on-chain.
        """


@dataclass(frozen=True)
class CovenantRegistryClientConfig:
    """Runtime configuration for one chain-specific registry client."""

    chain_id: int
    rpc_url: str
    contract_address: str
    private_key: str
    abi: list[dict[str, Any]]


class AsyncCovenantRegistryClient:
    """Async web3.py client for FacilityCovenantRegistry."""

    def __init__(self, config: CovenantRegistryClientConfig) -> None:
        """Create the async web3 and contract objects.

        Args:
            config: Chain-specific contract configuration.
        """

        self.chain_id = config.chain_id
        checksum_address = AsyncWeb3.to_checksum_address(config.contract_address)
        self.contract_address = str(checksum_address)
        self._web3 = AsyncWeb3(AsyncHTTPProvider(config.rpc_url))
        self._account = Account.from_key(config.private_key)
        self._contract = self._web3.eth.contract(address=checksum_address, abi=config.abi)

    async def publish_facility_report(
        self,
        *,
        facility_type: FacilityType,
        result: CovenantResult,
    ) -> CovenantPublication:
        """Publish a calculated covenant result on-chain.

        Args:
            facility_type: Facility associated with the covenant result.
            result: Calculated covenant output.

        Raises:
            CovenantPublicationError: If the transaction fails.

        Returns:
            CovenantPublication: Transaction metadata for the publication.
        """

        try:
            logger.info(
                "Publishing covenant report to registry for {facility_type}",
                facility_type=facility_type.value,
            )
            function = self._contract.functions.updateFacilityReport(
                facility_type.value,
                _rate_to_bps(result.computed_effective_rate),
                _status_to_contract_value(result.covenant_status),
                result.summary.total_assets_evaluated,
                result.included_assets,
                [asset.external_id for asset in result.excluded_assets],
            )
            transaction = await function.build_transaction(
                {
                    "chainId": self.chain_id,
                    "from": self._account.address,
                    "nonce": await self._web3.eth.get_transaction_count(self._account.address),
                }
            )
            signed = self._account.sign_transaction(transaction)
            raw_transaction = getattr(signed, "raw_transaction", None)
            if raw_transaction is None:
                raw_transaction = signed.rawTransaction
            transaction_hash = await self._web3.eth.send_raw_transaction(raw_transaction)
            receipt = await self._web3.eth.wait_for_transaction_receipt(transaction_hash)
        except Exception as exc:
            raise CovenantPublicationError(
                details=[{"facility_type": facility_type.value}],
                private_details=[{"facility_type": facility_type.value, "error": str(exc)}],
            ) from exc

        if receipt.get("status") != 1:
            raise CovenantPublicationError(
                details=[
                    {
                        "facility_type": facility_type.value,
                        "transaction_hash": _hex_with_prefix(transaction_hash.hex()),
                    }
                ],
            )

        logger.info(
            "Published covenant report to registry for {facility_type} in transaction {hash}",
            facility_type=facility_type.value,
            hash=_hex_with_prefix(transaction_hash.hex()),
        )
        return CovenantPublication(
            chain_id=self.chain_id,
            contract_address=self.contract_address,
            transaction_hash=_hex_with_prefix(transaction_hash.hex()),
        )

    async def get_facility_report(self, *, facility_type: FacilityType) -> OnChainCovenantResult:
        """Read the latest published covenant report for a facility.

        Args:
            facility_type: Facility to read from the registry.

        Raises:
            CovenantReportNotFoundError: If no report exists for the facility.
            CovenantRegistryReadError: If the contract read fails.

        Returns:
            OnChainCovenantResult: Latest report stored on-chain.
        """

        try:
            logger.info(
                "Reading covenant report from registry for {facility_type}",
                facility_type=facility_type.value,
            )
            exists = await self._contract.functions.reportExists(facility_type.value).call()
            if not exists:
                raise CovenantReportNotFoundError(facility_type=facility_type)
            report = await self._contract.functions.getFacilityReport(facility_type.value).call()
        except CovenantReportNotFoundError:
            raise
        except Exception as exc:
            raise CovenantRegistryReadError(
                details=[{"facility_type": facility_type.value}],
                private_details=[{"facility_type": facility_type.value, "error": str(exc)}],
            ) from exc

        return _report_to_schema(
            report=report,
            chain_id=self.chain_id,
            contract_address=self.contract_address,
        )


class CovenantRegistryClientRegistry:
    """Cache async registry clients by chain id."""

    def __init__(self) -> None:
        """Initialize an empty client registry.

        Returns:
            None: Initializes the registry.
        """

        self._clients: dict[int, AsyncCovenantRegistryClient] = {}

    def get_client(self, config: CovenantRegistryClientConfig) -> AsyncCovenantRegistryClient:
        """Return a cached client for the configured chain id.

        Args:
            config: Chain-specific contract configuration.

        Returns:
            AsyncCovenantRegistryClient: Cached or newly created client.
        """

        if config.chain_id not in self._clients:
            self._clients[config.chain_id] = AsyncCovenantRegistryClient(config)
        return self._clients[config.chain_id]

    def reset(self) -> None:
        """Clear cached clients.

        Returns:
            None: Empties the registry.
        """

        self._clients.clear()


_client_registry = CovenantRegistryClientRegistry()


def get_covenant_registry_client(settings: Settings) -> AsyncCovenantRegistryClient:
    """Return the chain-specific covenant registry client for settings.

    Args:
        settings: Application settings with chain and contract configuration.

    Raises:
        CovenantRegistryConfigurationError: If required contract settings are missing.

    Returns:
        AsyncCovenantRegistryClient: Cached registry client for the configured chain.
    """

    if not settings.covenant_registry_address:
        raise CovenantRegistryConfigurationError(
            private_details=[{"missing": "covenant_registry_address"}],
        )
    if not settings.covenant_registry_private_key:
        raise CovenantRegistryConfigurationError(
            private_details=[{"missing": "covenant_registry_private_key"}],
        )

    config = CovenantRegistryClientConfig(
        chain_id=settings.web3_chain_id,
        rpc_url=settings.web3_rpc_url,
        contract_address=settings.covenant_registry_address,
        private_key=settings.covenant_registry_private_key,
        abi=load_registry_abi(settings.covenant_registry_abi_path),
    )
    return _client_registry.get_client(config)


def reset_covenant_registry_clients() -> None:
    """Clear the global chain client registry.

    Returns:
        None: Empties cached clients.
    """

    _client_registry.reset()


def _rate_to_bps(rate: Decimal) -> int:
    """Convert a percentage rate to basis points.

    Args:
        rate: Decimal percentage rate from the covenant calculation.

    Returns:
        int: Rate represented in basis points.
    """

    return int((rate * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _hex_with_prefix(value: str) -> str:
    """Ensure a hex string uses the `0x` prefix.

    Args:
        value: Hex string returned by a web3 type.

    Returns:
        str: Hex string with `0x` prefix.
    """

    return value if value.startswith("0x") else f"0x{value}"


def _status_to_contract_value(status: CovenantStatus) -> int:
    """Convert the API status enum to the Solidity enum value.

    Args:
        status: Covenant status from the calculator.

    Returns:
        int: Solidity enum value.
    """

    return 0 if status is CovenantStatus.COMPLIANT else 1


def _status_from_contract_value(status: int) -> CovenantStatus:
    """Convert the Solidity enum value to the API status enum.

    Args:
        status: Solidity enum value.

    Returns:
        CovenantStatus: API covenant status.
    """

    return CovenantStatus.COMPLIANT if status == 0 else CovenantStatus.BREACH


def _report_to_schema(
    *,
    report: Any,
    chain_id: int,
    contract_address: str,
) -> OnChainCovenantResult:
    """Map a contract report tuple to the API schema.

    Args:
        report: Contract tuple returned by `getFacilityReport`.
        chain_id: Chain id used for the contract read.
        contract_address: Registry contract address.

    Returns:
        OnChainCovenantResult: API representation of the on-chain report.
    """

    effective_rate_bps = int(report[1])
    return OnChainCovenantResult(
        facility=report[0],
        effective_rate_bps=effective_rate_bps,
        computed_effective_rate=Decimal(effective_rate_bps) / Decimal("100"),
        covenant_status=_status_from_contract_value(int(report[2])),
        summary=CovenantSummary(
            total_assets_evaluated=int(report[3]),
            assets_included=int(report[4]),
            assets_excluded=int(report[5]),
        ),
        included_assets=list(report[6]),
        excluded_assets=list(report[7]),
        updated_at=int(report[8]),
        exists=bool(report[10]),
        chain_id=chain_id,
        contract_address=contract_address,
    )
