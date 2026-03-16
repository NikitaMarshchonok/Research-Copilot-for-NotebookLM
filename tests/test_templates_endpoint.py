from fastapi.testclient import TestClient

from app.main import app


def test_templates_endpoint_returns_list() -> None:
    client = TestClient(app)
    response = client.get("/templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
