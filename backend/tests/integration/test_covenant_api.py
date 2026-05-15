import json
from pathlib import Path

from fastapi.testclient import TestClient

from main import app


def load_json(path: Path) -> str:
    return json.dumps(json.loads(path.read_text()))


def test_covenant_endpoint_calculates_educa_with_real_data(data_dir: Path) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=load_json(data_dir / "facility_a_educa_isa.json"),
        headers={"X-Fence-Facility-Type": "educa"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "computed_effective_rate": 18.33,
        "covenant_status": "COMPLIANT",
        "summary": {
            "total_assets_evaluated": 8,
            "assets_included": 5,
            "assets_excluded": 3,
        },
        "included_assets": [
            "EDU-STU-10001",
            "EDU-STU-10002",
            "EDU-STU-10004",
            "EDU-STU-10005",
            "EDU-STU-10007",
        ],
        "excluded_assets": [
            {
                "external_id": "EDU-STU-10003",
                "reasons": [
                    "ineligible flag",
                    "loan_status mismatch: expected current",
                ],
            },
            {
                "external_id": "EDU-STU-10006",
                "reasons": [
                    "status mismatch: expected open",
                    "ineligible flag",
                    "loan_status mismatch: expected current",
                ],
            },
            {
                "external_id": "EDU-STU-10008",
                "reasons": ["missing interest_rate_percentage"],
            },
        ],
    }


def test_covenant_endpoint_calculates_payearly_with_real_data(data_dir: Path) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=load_json(data_dir / "facility_b_payearly_ewa.json"),
        headers={"X-Fence-Facility-Type": "payearly"},
    )

    assert response.status_code == 200
    assert response.json()["computed_effective_rate"] == 0.0
    assert response.json()["covenant_status"] == "COMPLIANT"


def test_covenant_endpoint_calculates_nomina_with_real_data(data_dir: Path) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=load_json(data_dir / "facility_c_nomina.json"),
        headers={"X-Fence-Facility-Type": "nomina"},
    )

    assert response.status_code == 200
    assert response.json()["computed_effective_rate"] == 3.39
    assert response.json()["covenant_status"] == "COMPLIANT"


def test_covenant_endpoint_returns_400_for_missing_header(data_dir: Path) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=load_json(data_dir / "facility_a_educa_isa.json"),
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "missing_facility_header",
        "message": "Missing X-Fence-Facility-Type header",
        "details": [],
    }


def test_covenant_endpoint_returns_400_for_invalid_header(data_dir: Path) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=load_json(data_dir / "facility_a_educa_isa.json"),
        headers={"X-Fence-Facility-Type": "unknown"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_facility_header",
        "message": "Invalid X-Fence-Facility-Type header",
        "details": [
            {
                "provided_value": "unknown",
                "allowed_values": ["educa", "payearly", "nomina"],
            }
        ],
    }


def test_covenant_endpoint_returns_422_for_header_body_mismatch(data_dir: Path) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=load_json(data_dir / "facility_a_educa_isa.json"),
        headers={"X-Fence-Facility-Type": "payearly"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "facility_payload_validation_error"
    assert body["message"] == "Payload does not match the declared facility schema"
    assert body["details"][0]["facility_type"] == "payearly"


def test_covenant_endpoint_returns_400_for_invalid_json() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content="{bad-json}",
        headers={"X-Fence-Facility-Type": "educa"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_json_payload",
        "message": "Payload is not valid JSON",
        "details": [],
    }


def test_covenant_endpoint_returns_400_for_non_array_json() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/covenants/calculate",
        content=json.dumps({"external_id": "EDU-1"}),
        headers={"X-Fence-Facility-Type": "educa"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_payload_type",
        "message": "Payload must be a JSON array of assets",
        "details": [],
    }
