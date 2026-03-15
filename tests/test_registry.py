from pathlib import Path

from app.models.notebook import NotebookCreate
from app.services.notebook_registry import NotebookRegistryService
from app.storage.json_store import JsonStore


def test_registry_add_and_select(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "notebooks.json", {"active_notebook_id": None, "items": []})
    service = NotebookRegistryService(store)

    notebook = service.add_notebook(
        NotebookCreate(
            name="Test notebook",
            url="https://notebooklm.google.com/notebook/test",
            tags=["ai"],
            description="Demo",
        )
    )
    service.select_active(notebook.id)
    active = service.get_active()

    assert active.id == notebook.id
    assert len(service.list_notebooks()) == 1
