from fastapi.testclient import TestClient

from app.main import app


def test_active_notebook_endpoint_shape() -> None:
    client = TestClient(app)
    response = client.get("/notebooks/active")
    assert response.status_code == 200
    body = response.json()
    assert "active_notebook_id" in body
    assert "notebook" in body
