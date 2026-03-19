from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.bundle_preset import BundlePresetCreateRequest
from app.services.bundle_preset_service import BundlePresetService
from app.storage.json_store import JsonStore


def test_bundle_presets_endpoint_returns_list() -> None:
    client = TestClient(app)
    response = client.get("/bundle-presets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_bundle_preset_service_add_and_get_item_types(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "bundle_presets.json", {"items": []})
    service = BundlePresetService(store)
    created = service.add_preset(
        BundlePresetCreateRequest(
            name="custom-pack",
            description="custom",
            item_types=["research", "ask"],
        )
    )
    assert created.name == "custom-pack"
    assert service.get_item_types("custom-pack") == ["research", "ask"]
