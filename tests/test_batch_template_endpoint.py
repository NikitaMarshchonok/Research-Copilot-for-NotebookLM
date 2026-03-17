from fastapi.testclient import TestClient

from app.main import app


def test_batch_template_endpoint_returns_batch_response_shape() -> None:
    client = TestClient(app)
    response = client.post(
        "/research/batch-template",
        json={
            "topics": ["mcp basics", "notebooklm setup"],
            "template_name": "summary",
            "continue_on_error": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert "items" in body
    assert "failures" in body
