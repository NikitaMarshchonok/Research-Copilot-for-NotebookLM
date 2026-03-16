from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotebookEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class NotebookCreate(BaseModel):
    name: str
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)
    description: str = ""


class NotebookSelectRequest(BaseModel):
    notebook_id: str


class NotebookRegistryState(BaseModel):
    active_notebook_id: Optional[str] = None
    items: List[NotebookEntry] = Field(default_factory=list)


class ActiveNotebookResponse(BaseModel):
    active_notebook_id: Optional[str] = None
    notebook: Optional[NotebookEntry] = None
