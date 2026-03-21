from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.notebook import NotebookRegistryState
from app.models.search_view import SearchViewCreateRequest
from app.models.snapshot import SnapshotCreateRequest
from app.services.bundle_preset_service import BundlePresetService
from app.services.export_service import ExportService
from app.services.notebook_registry import NotebookRegistryService
from app.services.notebooklm_client import StubNotebookLMClient
from app.services.research_service import ResearchService
from app.services.search_view_service import SearchViewService
from app.services.template_service import TemplateService
from app.storage.file_store import FileStore
from app.storage.json_store import JsonStore


def test_snapshots_endpoint_status() -> None:
    client = TestClient(app)
    response = client.get("/snapshots")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    diff_response = client.post(
        "/snapshots/diff",
        json={"from_snapshot_id": "missing-a", "to_snapshot_id": "missing-b"},
    )
    assert diff_response.status_code == 400


def test_snapshot_creation_and_changelog(tmp_path: Path) -> None:
    notebooks_store = JsonStore(
        tmp_path / "notebooks.json",
        default_value=NotebookRegistryState().model_dump(mode="json"),
    )
    history_store = JsonStore(tmp_path / "history.json", default_value={"items": []})
    templates_store = JsonStore(tmp_path / "templates.json", default_value={"items": []})
    bundle_presets_store = JsonStore(tmp_path / "bundle_presets.json", default_value={"items": []})
    search_views_store = JsonStore(tmp_path / "search_views.json", default_value={"items": []})
    snapshots_store = JsonStore(tmp_path / "snapshots.json", default_value={"items": []})

    service = ResearchService(
        registry=NotebookRegistryService(notebooks_store),
        template_service=TemplateService(templates_store),
        bundle_preset_service=BundlePresetService(bundle_presets_store),
        search_view_service=SearchViewService(search_views_store),
        notebooklm_client=StubNotebookLMClient(),
        export_service=ExportService(FileStore(tmp_path / "outputs")),
        history_store=history_store,
        snapshots_store=snapshots_store,
    )

    service.add_search_view(
        SearchViewCreateRequest(
            name="history-all",
            scope="history",
            description="all history",
        )
    )

    history_store.write(
        {
            "items": [
                {"type": "ask", "payload": {"id": "a1", "question": "q1"}},
                {"type": "research", "payload": {"id": "r1", "topic": "t1"}},
            ]
        }
    )
    first = service.create_snapshot(SnapshotCreateRequest(view_name="history-all"))
    assert first.item_count == 2
    assert len(first.changelog.added_ids) == 2

    history_store.write(
        {
            "items": [
                {"type": "research", "payload": {"id": "r1", "topic": "t1"}},
                {"type": "research", "payload": {"id": "r2", "topic": "t2"}},
            ]
        }
    )
    second = service.create_snapshot(SnapshotCreateRequest(view_name="history-all"))
    assert "r2" in second.changelog.added_ids
    assert "a1" in second.changelog.removed_ids

    diff = service.diff_snapshots(first.id, second.id)
    assert "r2" in diff.added_ids
    assert "a1" in diff.removed_ids
    assert diff.summary["net_change"] == 0
    assert diff.summary["added_count"] == 1
    assert diff.summary["removed_count"] == 1
    assert diff.summary["common_count"] == 1

    exported = service.export_snapshot_diff(first.id, second.id)
    assert "markdown" in exported
    assert "json" in exported

    latest_diff = service.diff_latest_snapshots(view_name="history-all")
    assert latest_diff.from_snapshot_id == first.id
    assert latest_diff.to_snapshot_id == second.id

    latest_export = service.export_latest_snapshot_diff(view_name="history-all")
    assert "markdown" in latest_export
    assert "json" in latest_export

    brief = service.snapshot_diff_brief(first.id, second.id, top_items=1)
    assert "history-all" in brief.brief
    assert len(brief.top_added_ids) <= 1
    assert len(brief.top_removed_ids) <= 1

    latest_brief = service.latest_snapshot_diff_brief(view_name="history-all", top_items=1)
    assert latest_brief.from_snapshot_id == first.id
    assert latest_brief.to_snapshot_id == second.id

    digest = service.snapshot_diff_digest(view_names=["history-all"], top_items=1)
    assert digest.included_count == 1
    assert digest.skipped_count == 0
    assert digest.items[0].view_name == "history-all"

    digest_with_missing = service.snapshot_diff_digest(
        view_names=["history-all", "unknown-view"],
        top_items=1,
        include_missing=True,
    )
    assert digest_with_missing.included_count == 1
    assert digest_with_missing.skipped_count == 1

    digest_export = service.export_snapshot_diff_digest(view_names=["history-all"], top_items=1)
    assert "markdown" in digest_export
    assert "json" in digest_export

    history_store.write(
        {
            "items": [
                {"type": "research", "payload": {"id": "r1", "topic": "t1"}},
                {"type": "research", "payload": {"id": "r2", "topic": "t2"}},
                {"type": "research", "payload": {"id": "r3", "topic": "t3"}},
            ]
        }
    )
    third = service.create_snapshot(SnapshotCreateRequest(view_name="history-all"))
    assert third.item_count == 3

    trend = service.snapshot_trend(view_name="history-all", limit=5)
    assert trend.view_name == "history-all"
    assert trend.compared_pairs == 2
    assert len(trend.points) == 3
    assert trend.points[-1].added_count_from_previous >= 1

    trend_export = service.export_snapshot_trend(view_name="history-all", limit=5)
    assert "markdown" in trend_export
    assert "json" in trend_export
