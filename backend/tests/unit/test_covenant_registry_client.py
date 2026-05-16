from decimal import Decimal

from core.clients.covenant_registry import (
    _hex_with_prefix,
    _rate_to_bps,
    _status_from_contract_value,
    _status_to_contract_value,
)
from core.utils.contract_abi import load_registry_abi
from schemas.covenant import CovenantStatus


def test_registry_abi_loader_reads_checked_in_abi() -> None:
    abi = load_registry_abi()

    function_names = {entry["name"] for entry in abi if entry.get("type") == "function"}
    assert function_names == {
        "getFacilityReport",
        "reportExists",
        "updateFacilityReport",
    }


def test_registry_client_maps_rate_to_basis_points() -> None:
    assert _rate_to_bps(Decimal("18.33")) == 1833
    assert _rate_to_bps(Decimal("3.385")) == 339


def test_registry_client_maps_covenant_status_values() -> None:
    assert _status_to_contract_value(CovenantStatus.COMPLIANT) == 0
    assert _status_to_contract_value(CovenantStatus.BREACH) == 1
    assert _status_from_contract_value(0) == CovenantStatus.COMPLIANT
    assert _status_from_contract_value(1) == CovenantStatus.BREACH


def test_registry_client_normalizes_transaction_hash_prefix() -> None:
    assert _hex_with_prefix("abc") == "0xabc"
    assert _hex_with_prefix("0xabc") == "0xabc"
