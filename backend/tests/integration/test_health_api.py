from fastapi.testclient import TestClient


def test_health_endpoint_returns_expected_payload(test_app: TestClient) -> None:
    response = test_app.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "Fence Tech Challenge Backend",
        "environment": "local",
    }
