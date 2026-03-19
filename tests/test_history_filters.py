from pathlib import Path

from app.models.notebook import NotebookRegistryState
from app.services.bundle_preset_service import BundlePresetService
from app.services.export_service import ExportService
from app.services.notebook_registry import NotebookRegistryService
from app.services.notebooklm_client import StubNotebookLMClient
from app.services.research_service import ResearchService
from app.services.template_service import TemplateService
from app.storage.file_store import FileStore
from app.storage.json_store import JsonStore


def test_history_filters_by_type_tag_and_query(tmp_path: Path) -> None:
    notebooks_store = JsonStore(
        tmp_path / "notebooks.json",
        default_value=NotebookRegistryState().model_dump(mode="json"),
    )
    history_store = JsonStore(tmp_path / "history.json", default_value={"items": []})
    templates_store = JsonStore(tmp_path / "templates.json", default_value={"items": []})
    bundle_presets_store = JsonStore(tmp_path / "bundle_presets.json", default_value={"items": []})
    service = ResearchService(
        registry=NotebookRegistryService(notebooks_store),
        template_service=TemplateService(templates_store),
        bundle_preset_service=BundlePresetService(bundle_presets_store),
        notebooklm_client=StubNotebookLMClient(),
        export_service=ExportService(FileStore(tmp_path / "outputs")),
        history_store=history_store,
    )

    history_store.write(
        {
            "items": [
                {
                    "type": "ask",
                    "payload": {
                        "id": "a1",
                        "question": "quick question",
                        "tags": ["quick"],
                        "created_at": "2026-01-01T00:00:00Z",
                    },
                },
                {
                    "type": "research",
                    "payload": {
                        "id": "r1",
                        "topic": "deep topic",
                        "tags": ["deep"],
                        "created_at": "2026-01-02T00:00:00Z",
                    },
                },
            ]
        }
    )

    assert len(service.list_history(item_type="ask")) == 1
    assert len(service.list_history(tag="deep")) == 1
    assert len(service.list_history(query="quick")) == 1
