from fastapi.testclient import TestClient

from main import app


def test_health_endpoint_returns_expected_payload() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "Fence Tech Challenge Backend",
        "environment": "local",
    }
