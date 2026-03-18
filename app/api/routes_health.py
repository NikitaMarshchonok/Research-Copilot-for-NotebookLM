from __future__ import annotations

from fastapi import APIRouter, Depends

from app.bootstrap import ServiceContainer, build_container
router = APIRouter(tags=["health"])


def get_container() -> ServiceContainer:
    return build_container()


@router.get("/health")
def health(container: ServiceContainer = Depends(get_container)) -> dict[str, str]:
    return {"status": "ok", "workspace": container.active_workspace}
