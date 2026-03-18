from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class WorkspaceCreateRequest(BaseModel):
    name: str
    description: str = ""


class WorkspaceSelectRequest(BaseModel):
    name: str


class WorkspaceRegistryState(BaseModel):
    active_workspace: str = "default"
    items: list[WorkspaceEntry] = Field(default_factory=list)


class WorkspaceCurrentResponse(BaseModel):
    active_workspace: str
    data_path: str
    outputs_path: str
    workspace: Optional[WorkspaceEntry] = None


class WorkspaceContext(BaseModel):
    name: str
    data_path: Path
    outputs_path: Path
