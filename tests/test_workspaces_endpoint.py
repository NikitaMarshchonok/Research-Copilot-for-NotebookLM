from fastapi.testclient import TestClient

from app.main import app


def test_workspaces_current_endpoint_shape() -> None:
    client = TestClient(app)
    response = client.get("/workspaces/current")
    assert response.status_code == 200
    body = response.json()
    assert "active_workspace" in body
    assert "data_path" in body
    assert "outputs_path" in body
