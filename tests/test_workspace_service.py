from pathlib import Path

from app.models.workspace import WorkspaceCreateRequest
from app.services.workspace_service import WorkspaceService
from app.storage.json_store import JsonStore


def test_workspace_service_create_select_context(tmp_path: Path) -> None:
    class FakeSettings:
        data_path = tmp_path / "data"
        outputs_path = tmp_path / "outputs"
        workspaces_path = tmp_path / "workspaces"

    settings = FakeSettings()
    store = JsonStore(tmp_path / "data" / "workspaces.json", {"active_workspace": "default", "items": []})
    service = WorkspaceService(settings=settings, registry_store=store)

    service.create_workspace(WorkspaceCreateRequest(name="client-a", description=""))
    selected = service.select_workspace("client-a")
    context = service.get_active_context()

    assert selected.name == "client-a"
    assert context.name == "client-a"
    assert context.data_path.exists()
    assert context.outputs_path.exists()
