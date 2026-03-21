from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.bootstrap import ServiceContainer, build_container
from app.models.artifact import ArtifactItem
from app.models.bundle_preset import BundlePresetCreateRequest, BundlePresetEntry
from app.models.export import (
    BundleExportRequest,
    BundleExportResponse,
    ExportRequest,
    ExportResponse,
    LatestExportRequest,
)
from app.models.history import HistoryItem, HistorySummary
from app.models.query import AskRequest, AskResponse
from app.models.report import BatchResearchResponse, ResearchRequest, ResearchResponse
from app.models.search_view import SearchViewCreateRequest, SearchViewEntry, SearchViewRunResponse
from app.models.snapshot import (
    SnapshotCreateRequest,
    SnapshotDiffBriefResponse,
    SnapshotDiffDigestExportResponse,
    SnapshotDiffDigestRequest,
    SnapshotDiffDigestResponse,
    SnapshotDiffExportResponse,
    SnapshotDiffRequest,
    SnapshotDiffResponse,
    SnapshotEntry,
    SnapshotListItem,
    SnapshotTrendExportResponse,
    SnapshotTrendRequest,
    SnapshotTrendResponse,
)
from app.models.template import (
    RunBatchTemplateRequest,
    RunTemplateRequest,
    TemplateCreateRequest,
    TemplateEntry,
)

router = APIRouter(tags=["research"])


def get_container() -> ServiceContainer:
    return build_container()


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, container: ServiceContainer = Depends(get_container)) -> AskResponse:
    return container.research_service.ask(payload)


@router.post("/research", response_model=ResearchResponse)
def research(
    payload: ResearchRequest, container: ServiceContainer = Depends(get_container)
) -> ResearchResponse:
    return container.research_service.research(payload)


@router.post("/export", response_model=ExportResponse)
def export_item(
    payload: ExportRequest, container: ServiceContainer = Depends(get_container)
) -> ExportResponse:
    paths = container.research_service.export_from_history(payload.history_id)
    return ExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.post("/exports", response_model=ExportResponse)
def export_item_plural(
    payload: ExportRequest, container: ServiceContainer = Depends(get_container)
) -> ExportResponse:
    paths = container.research_service.export_from_history(payload.history_id)
    return ExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.post("/exports/latest", response_model=ExportResponse)
def export_latest(
    payload: LatestExportRequest, container: ServiceContainer = Depends(get_container)
) -> ExportResponse:
    paths = container.research_service.export_latest_artifact(
        item_type=payload.item_type,
        template_name=payload.template_name,
        tag=payload.tag,
        query=payload.query,
    )
    return ExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.post("/exports/bundle", response_model=BundleExportResponse)
def export_bundle(
    payload: BundleExportRequest, container: ServiceContainer = Depends(get_container)
) -> BundleExportResponse:
    paths = container.research_service.export_artifact_bundle(
        bundle_name=payload.bundle_name,
        template_name=payload.template_name,
    )
    return BundleExportResponse(
        markdown=str(paths["markdown"]),
        json_path=str(paths["json"]),
        included_count=int(paths["included_count"]),
    )


@router.get("/bundle-presets", response_model=list[BundlePresetEntry])
def list_bundle_presets(container: ServiceContainer = Depends(get_container)) -> list[BundlePresetEntry]:
    return container.research_service.list_bundle_presets()


@router.post("/bundle-presets", response_model=BundlePresetEntry)
def add_bundle_preset(
    payload: BundlePresetCreateRequest, container: ServiceContainer = Depends(get_container)
) -> BundlePresetEntry:
    return container.research_service.add_bundle_preset(payload)


@router.delete("/bundle-presets/{preset_name}")
def delete_bundle_preset(
    preset_name: str, container: ServiceContainer = Depends(get_container)
) -> dict[str, str]:
    container.research_service.delete_bundle_preset(preset_name)
    return {"status": "deleted", "preset": preset_name}


@router.get("/search-views", response_model=list[SearchViewEntry])
def list_search_views(container: ServiceContainer = Depends(get_container)) -> list[SearchViewEntry]:
    return container.research_service.list_search_views()


@router.post("/search-views", response_model=SearchViewEntry)
def add_search_view(
    payload: SearchViewCreateRequest, container: ServiceContainer = Depends(get_container)
) -> SearchViewEntry:
    return container.research_service.add_search_view(payload)


@router.delete("/search-views/{view_name}")
def delete_search_view(
    view_name: str, container: ServiceContainer = Depends(get_container)
) -> dict[str, str]:
    container.research_service.delete_search_view(view_name)
    return {"status": "deleted", "view": view_name}


@router.get("/search-views/{view_name}/run", response_model=SearchViewRunResponse)
def run_search_view(
    view_name: str, container: ServiceContainer = Depends(get_container)
) -> SearchViewRunResponse:
    return container.research_service.run_search_view(view_name)


@router.post("/snapshots", response_model=SnapshotEntry)
def create_snapshot(
    payload: SnapshotCreateRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotEntry:
    return container.research_service.create_snapshot(payload)


@router.get("/snapshots", response_model=list[SnapshotListItem])
def list_snapshots(
    view_name: str | None = Query(default=None, description="Filter by saved view name"),
    container: ServiceContainer = Depends(get_container),
) -> list[SnapshotListItem]:
    return container.research_service.list_snapshots(view_name=view_name)


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotEntry)
def get_snapshot(
    snapshot_id: str, container: ServiceContainer = Depends(get_container)
) -> SnapshotEntry:
    return container.research_service.get_snapshot(snapshot_id)


@router.post("/snapshots/diff", response_model=SnapshotDiffResponse)
def diff_snapshots(
    payload: SnapshotDiffRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotDiffResponse:
    return container.research_service.diff_snapshots(
        from_snapshot_id=payload.from_snapshot_id,
        to_snapshot_id=payload.to_snapshot_id,
    )


@router.post("/snapshots/diff/export", response_model=SnapshotDiffExportResponse)
def export_snapshot_diff(
    payload: SnapshotDiffRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotDiffExportResponse:
    paths = container.research_service.export_snapshot_diff(
        from_snapshot_id=payload.from_snapshot_id,
        to_snapshot_id=payload.to_snapshot_id,
    )
    return SnapshotDiffExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.get("/snapshots/diff/latest", response_model=SnapshotDiffResponse)
def diff_latest_snapshots(
    view_name: str = Query(..., description="Saved view name"),
    container: ServiceContainer = Depends(get_container),
) -> SnapshotDiffResponse:
    return container.research_service.diff_latest_snapshots(view_name=view_name)


@router.post("/snapshots/diff/latest/export", response_model=SnapshotDiffExportResponse)
def export_latest_snapshot_diff(
    view_name: str = Query(..., description="Saved view name"),
    container: ServiceContainer = Depends(get_container),
) -> SnapshotDiffExportResponse:
    paths = container.research_service.export_latest_snapshot_diff(view_name=view_name)
    return SnapshotDiffExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.post("/snapshots/diff/brief", response_model=SnapshotDiffBriefResponse)
def snapshot_diff_brief(
    payload: SnapshotDiffRequest,
    top_items: int = Query(default=5, ge=1, le=50),
    container: ServiceContainer = Depends(get_container),
) -> SnapshotDiffBriefResponse:
    return container.research_service.snapshot_diff_brief(
        from_snapshot_id=payload.from_snapshot_id,
        to_snapshot_id=payload.to_snapshot_id,
        top_items=top_items,
    )


@router.get("/snapshots/diff/latest/brief", response_model=SnapshotDiffBriefResponse)
def latest_snapshot_diff_brief(
    view_name: str = Query(..., description="Saved view name"),
    top_items: int = Query(default=5, ge=1, le=50),
    container: ServiceContainer = Depends(get_container),
) -> SnapshotDiffBriefResponse:
    return container.research_service.latest_snapshot_diff_brief(
        view_name=view_name,
        top_items=top_items,
    )


@router.post("/snapshots/diff/digest", response_model=SnapshotDiffDigestResponse)
def snapshot_diff_digest(
    payload: SnapshotDiffDigestRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotDiffDigestResponse:
    return container.research_service.snapshot_diff_digest(
        view_names=payload.view_names,
        top_items=payload.top_items,
        include_missing=payload.include_missing,
    )


@router.post("/snapshots/diff/digest/export", response_model=SnapshotDiffDigestExportResponse)
def export_snapshot_diff_digest(
    payload: SnapshotDiffDigestRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotDiffDigestExportResponse:
    paths = container.research_service.export_snapshot_diff_digest(
        view_names=payload.view_names,
        top_items=payload.top_items,
        include_missing=payload.include_missing,
    )
    return SnapshotDiffDigestExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.post("/snapshots/trend", response_model=SnapshotTrendResponse)
def snapshot_trend(
    payload: SnapshotTrendRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotTrendResponse:
    return container.research_service.snapshot_trend(
        view_name=payload.view_name,
        limit=payload.limit,
    )


@router.post("/snapshots/trend/export", response_model=SnapshotTrendExportResponse)
def export_snapshot_trend(
    payload: SnapshotTrendRequest, container: ServiceContainer = Depends(get_container)
) -> SnapshotTrendExportResponse:
    paths = container.research_service.export_snapshot_trend(
        view_name=payload.view_name,
        limit=payload.limit,
    )
    return SnapshotTrendExportResponse(markdown=paths["markdown"], json_path=paths["json"])


@router.get("/history", response_model=list[HistorySummary])
def list_history(
    item_type: str | None = Query(default=None, description="ask|research|batch_research"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    query: str | None = Query(default=None, description="Search in title"),
    container: ServiceContainer = Depends(get_container),
) -> list[HistorySummary]:
    return container.research_service.list_history(item_type=item_type, tag=tag, query=query)


@router.get("/artifacts", response_model=list[ArtifactItem])
def list_artifacts(
    item_type: str | None = Query(default=None, description="ask|research|batch_research"),
    template_name: str | None = Query(default=None, description="Filter by template name"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    query: str | None = Query(default=None, description="Search in title"),
    container: ServiceContainer = Depends(get_container),
) -> list[ArtifactItem]:
    return container.research_service.list_artifacts(
        item_type=item_type,
        template_name=template_name,
        tag=tag,
        query=query,
    )


@router.get("/artifacts/latest", response_model=ArtifactItem)
def get_latest_artifact(
    item_type: str | None = Query(default=None, description="ask|research|batch_research"),
    template_name: str | None = Query(default=None, description="Filter by template name"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    query: str | None = Query(default=None, description="Search in title"),
    container: ServiceContainer = Depends(get_container),
) -> ArtifactItem:
    return container.research_service.get_latest_artifact(
        item_type=item_type,
        template_name=template_name,
        tag=tag,
        query=query,
    )


@router.get("/history/{history_id}", response_model=HistoryItem)
def get_history_item(
    history_id: str, container: ServiceContainer = Depends(get_container)
) -> HistoryItem:
    return container.research_service.get_history_item(history_id)


@router.get("/templates", response_model=list[TemplateEntry])
def list_templates(container: ServiceContainer = Depends(get_container)) -> list[TemplateEntry]:
    return container.template_service.list_templates()


@router.post("/templates", response_model=TemplateEntry)
def add_template(
    payload: TemplateCreateRequest, container: ServiceContainer = Depends(get_container)
) -> TemplateEntry:
    return container.template_service.add_template(payload)


@router.post("/research/template", response_model=ResearchResponse)
def research_from_template(
    payload: RunTemplateRequest, container: ServiceContainer = Depends(get_container)
) -> ResearchResponse:
    return container.research_service.research_from_template(
        topic=payload.topic,
        template_name=payload.template_name,
        notebook_id=payload.notebook_id,
        artifact_type=payload.artifact_type,
        tags=payload.tags,
    )


@router.post("/research/batch-template", response_model=BatchResearchResponse)
def research_batch_from_template(
    payload: RunBatchTemplateRequest, container: ServiceContainer = Depends(get_container)
) -> BatchResearchResponse:
    return container.research_service.batch_research_from_template(
        topics=payload.topics,
        template_name=payload.template_name,
        notebook_id=payload.notebook_id,
        artifact_type=payload.artifact_type,
        tags=payload.tags,
        continue_on_error=payload.continue_on_error,
    )
