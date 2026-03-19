from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.search_view import SearchViewCreateRequest
from app.services.search_view_service import SearchViewService
from app.storage.json_store import JsonStore


def test_search_views_endpoint_returns_list() -> None:
    client = TestClient(app)
    response = client.get("/search-views")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_view_service_add_get_delete(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "search_views.json", {"items": []})
    service = SearchViewService(store)

    created = service.add_view(
        SearchViewCreateRequest(
            name="research-deep",
            scope="history",
            item_type="research",
            tag="deep",
            query="mcp",
            description="deep research list",
        )
    )
    assert created.name == "research-deep"

    fetched = service.get_view("research-deep")
    assert fetched.scope == "history"
    assert fetched.tag == "deep"

    service.delete_view("research-deep")
    assert service.list_views() == []
