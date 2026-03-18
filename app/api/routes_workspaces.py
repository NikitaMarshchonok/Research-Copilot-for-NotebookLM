from __future__ import annotations

from fastapi import APIRouter, Depends

from app.bootstrap import ServiceContainer, build_container
from app.models.workspace import (
    WorkspaceCreateRequest,
    WorkspaceCurrentResponse,
    WorkspaceEntry,
    WorkspaceSelectRequest,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_container() -> ServiceContainer:
    return build_container()


@router.get("", response_model=list[WorkspaceEntry])
def list_workspaces(container: ServiceContainer = Depends(get_container)) -> list[WorkspaceEntry]:
    return container.workspace_service.list_workspaces()


@router.post("", response_model=WorkspaceEntry)
def create_workspace(
    payload: WorkspaceCreateRequest, container: ServiceContainer = Depends(get_container)
) -> WorkspaceEntry:
    return container.workspace_service.create_workspace(payload)


@router.post("/select", response_model=WorkspaceEntry)
def select_workspace(
    payload: WorkspaceSelectRequest, container: ServiceContainer = Depends(get_container)
) -> WorkspaceEntry:
    return container.workspace_service.select_workspace(payload.name)


@router.get("/current", response_model=WorkspaceCurrentResponse)
def get_current_workspace(
    container: ServiceContainer = Depends(get_container),
) -> WorkspaceCurrentResponse:
    return container.workspace_service.get_current_response()
