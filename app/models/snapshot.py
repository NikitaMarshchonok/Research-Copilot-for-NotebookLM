from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SnapshotDelta(BaseModel):
    added_ids: list[str] = Field(default_factory=list)
    removed_ids: list[str] = Field(default_factory=list)


class SnapshotEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    view_name: str
    scope: str
    item_count: int
    changelog: SnapshotDelta = Field(default_factory=SnapshotDelta)
    items: list[dict[str, Any]] = Field(default_factory=list)
    output_markdown_path: str | None = None
    output_json_path: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class SnapshotCreateRequest(BaseModel):
    view_name: str


class SnapshotListItem(BaseModel):
    id: str
    view_name: str
    scope: str
    item_count: int
    created_at: datetime
    output_markdown_path: str | None = None
    output_json_path: str | None = None
