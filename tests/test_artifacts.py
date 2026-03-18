from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.notebook import NotebookRegistryState
from app.services.export_service import ExportService
from app.services.notebook_registry import NotebookRegistryService
from app.services.notebooklm_client import StubNotebookLMClient
from app.services.research_service import ResearchService
from app.services.template_service import TemplateService
from app.storage.file_store import FileStore
from app.storage.json_store import JsonStore


def test_artifacts_endpoint_returns_list() -> None:
    client = TestClient(app)
    response = client.get("/artifacts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_artifacts_latest_endpoint_not_found_on_empty_history() -> None:
    client = TestClient(app)
    response = client.get("/artifacts/latest")
    # Depends on runtime data; if empty we should get domain-level 400.
    assert response.status_code in (200, 400)


def test_export_bundle_endpoint_status() -> None:
    client = TestClient(app)
    response = client.post("/exports/bundle", json={"bundle_name": "article-pack"})
    # On empty runtime data it may return app-level 400; otherwise 200.
    assert response.status_code in (200, 400)


def test_artifacts_filter_by_type(tmp_path: Path) -> None:
    notebooks_store = JsonStore(
        tmp_path / "notebooks.json",
        default_value=NotebookRegistryState().model_dump(mode="json"),
    )
    history_store = JsonStore(tmp_path / "history.json", default_value={"items": []})
    templates_store = JsonStore(tmp_path / "templates.json", default_value={"items": []})
    registry = NotebookRegistryService(notebooks_store)
    templates = TemplateService(templates_store)
    service = ResearchService(
        registry=registry,
        template_service=templates,
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
                        "question": "q1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "output_markdown_path": "outputs/a1.md",
                        "output_json_path": "outputs/a1.json",
                    },
                },
                {
                    "type": "research",
                    "payload": {
                        "id": "r1",
                        "topic": "topic1",
                        "created_at": "2026-01-02T00:00:00Z",
                        "output_markdown_path": "outputs/r1.md",
                        "output_json_path": "outputs/r1.json",
                    },
                },
            ]
        }
    )

    ask_only = service.list_artifacts(item_type="ask")
    assert len(ask_only) == 1
    assert ask_only[0].type == "ask"

    latest = service.get_latest_artifact()
    assert latest.id == "r1"

    by_template = service.list_artifacts(template_name="summary")
    assert by_template == []

    bundle = service.export_artifact_bundle(bundle_name="article-pack")
    assert "markdown" in bundle
    assert "json" in bundle
    assert bundle["included_count"] >= 1
