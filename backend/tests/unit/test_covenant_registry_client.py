from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.clients.covenant_registry import (
    _hex_with_prefix,
    _rate_to_bps,
    _report_to_schema,
    _status_from_contract_value,
    _status_to_contract_value,
)
from core.utils.contract_abi import load_registry_abi
from schemas.covenant import ContractFacilityReport, CovenantStatus


def test_registry_abi_loader_reads_checked_in_abi() -> None:
    abi = load_registry_abi()

    functions = {entry["name"]: entry for entry in abi if entry.get("type") == "function"}
    assert {"getFacilityReport", "reportExists", "updateFacilityReport"} <= set(functions)

    update_report = functions["updateFacilityReport"]
    assert update_report["inputs"][5]["type"] == "tuple[]"
    assert update_report["inputs"][5]["components"] == [
        {
            "name": "externalId",
            "type": "string",
            "internalType": "string",
        },
        {
            "name": "reasons",
            "type": "string[]",
            "internalType": "string[]",
        },
    ]

    get_report = functions["getFacilityReport"]
    excluded_assets_output = get_report["outputs"][0]["components"][7]
    assert excluded_assets_output["name"] == "excludedAssets"
    assert excluded_assets_output["type"] == "tuple[]"
    assert excluded_assets_output["components"] == [
        {
            "name": "externalId",
            "type": "string",
            "internalType": "string",
        },
        {
            "name": "reasons",
            "type": "string[]",
            "internalType": "string[]",
        },
    ]


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


def test_contract_facility_report_validates_summary_consistency() -> None:
    with pytest.raises(ValidationError):
        ContractFacilityReport.model_validate(
            (
                "educa",
                1833,
                0,
                3,
                1,
                1,
                ["asset-001"],
                [("asset-002", ["ineligible flag"])],
                12345,
                "0x000000000000000000000000000000000000beef",
                True,
            )
        )


def test_report_to_schema_maps_nested_excluded_assets() -> None:
    report = _report_to_schema(
        report=(
            "educa",
            1833,
            0,
            3,
            1,
            2,
            ["asset-001"],
            [
                ("asset-002", ["ineligible flag", "missing interest_rate_percentage"]),
                ("asset-003", ["status mismatch: expected current"]),
            ],
            12345,
            "0x000000000000000000000000000000000000beef",
            True,
        ),
        chain_id=31337,
        contract_address="0x0000000000000000000000000000000000000001",
    )

    assert report.facility == "educa"
    assert report.summary.total_assets_evaluated == 3
    assert report.summary.assets_included == 1
    assert report.summary.assets_excluded == 2
    assert report.excluded_assets[0].external_id == "asset-002"
    assert report.excluded_assets[0].reasons == [
        "ineligible flag",
        "missing interest_rate_percentage",
    ]
    assert report.excluded_assets[1].external_id == "asset-003"
    assert report.excluded_assets[1].reasons == [
        "status mismatch: expected current",
    ]
