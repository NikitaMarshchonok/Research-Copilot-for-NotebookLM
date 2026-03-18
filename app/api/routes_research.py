from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.bootstrap import ServiceContainer, build_container
from app.models.artifact import ArtifactItem
from app.models.export import ExportRequest, ExportResponse
from app.models.history import HistoryItem, HistorySummary
from app.models.query import AskRequest, AskResponse
from app.models.report import BatchResearchResponse, ResearchRequest, ResearchResponse
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


@router.get("/history", response_model=list[HistorySummary])
def list_history(container: ServiceContainer = Depends(get_container)) -> list[HistorySummary]:
    return container.research_service.list_history()


@router.get("/artifacts", response_model=list[ArtifactItem])
def list_artifacts(
    item_type: str | None = Query(default=None, description="ask|research|batch_research"),
    container: ServiceContainer = Depends(get_container),
) -> list[ArtifactItem]:
    return container.research_service.list_artifacts(item_type=item_type)


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
        continue_on_error=payload.continue_on_error,
    )
