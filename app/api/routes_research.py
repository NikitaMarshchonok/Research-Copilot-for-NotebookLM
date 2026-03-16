from __future__ import annotations

from fastapi import APIRouter, Depends

from app.bootstrap import ServiceContainer, build_container
from app.models.export import ExportRequest, ExportResponse
from app.models.history import HistoryItem, HistorySummary
from app.models.query import AskRequest, AskResponse
from app.models.report import ResearchRequest, ResearchResponse

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


@router.get("/history/{history_id}", response_model=HistoryItem)
def get_history_item(
    history_id: str, container: ServiceContainer = Depends(get_container)
) -> HistoryItem:
    return container.research_service.get_history_item(history_id)
