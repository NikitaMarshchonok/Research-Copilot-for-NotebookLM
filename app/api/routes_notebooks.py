from __future__ import annotations

from fastapi import APIRouter, Depends

from app.bootstrap import ServiceContainer, build_container
from app.models.notebook import NotebookCreate, NotebookEntry, NotebookSelectRequest

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


def get_container() -> ServiceContainer:
    return build_container()


@router.get("", response_model=list[NotebookEntry])
def list_notebooks(container: ServiceContainer = Depends(get_container)) -> list[NotebookEntry]:
    return container.notebook_registry.list_notebooks()


@router.post("", response_model=NotebookEntry)
def add_notebook(
    payload: NotebookCreate, container: ServiceContainer = Depends(get_container)
) -> NotebookEntry:
    return container.notebook_registry.add_notebook(payload)


@router.post("/select", response_model=NotebookEntry)
def select_notebook(
    payload: NotebookSelectRequest, container: ServiceContainer = Depends(get_container)
) -> NotebookEntry:
    return container.notebook_registry.select_active(payload.notebook_id)
