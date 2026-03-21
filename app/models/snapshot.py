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


class SnapshotDiffRequest(BaseModel):
    from_snapshot_id: str
    to_snapshot_id: str


class SnapshotDiffResponse(BaseModel):
    from_snapshot_id: str
    to_snapshot_id: str
    from_view_name: str
    to_view_name: str
    from_item_count: int
    to_item_count: int
    added_ids: list[str] = Field(default_factory=list)
    removed_ids: list[str] = Field(default_factory=list)
    common_ids: list[str] = Field(default_factory=list)
    summary: dict[str, float | int] = Field(default_factory=dict)


class SnapshotDiffExportResponse(BaseModel):
    markdown: str
    json_path: str


class SnapshotDiffBriefResponse(BaseModel):
    from_snapshot_id: str
    to_snapshot_id: str
    view_name: str
    brief: str
    added_count: int
    removed_count: int
    common_count: int
    top_added_ids: list[str] = Field(default_factory=list)
    top_removed_ids: list[str] = Field(default_factory=list)


class SnapshotDiffDigestRequest(BaseModel):
    view_names: list[str] = Field(default_factory=list)
    top_items: int = 5
    include_missing: bool = True


class SnapshotDiffDigestSkipped(BaseModel):
    view_name: str
    reason: str


class SnapshotDiffDigestResponse(BaseModel):
    generated_for_views: list[str] = Field(default_factory=list)
    included_count: int
    skipped_count: int
    items: list[SnapshotDiffBriefResponse] = Field(default_factory=list)
    skipped: list[SnapshotDiffDigestSkipped] = Field(default_factory=list)


class SnapshotDiffDigestExportResponse(BaseModel):
    markdown: str
    json_path: str


class SnapshotTrendPoint(BaseModel):
    snapshot_id: str
    created_at: datetime
    item_count: int
    added_count_from_previous: int
    removed_count_from_previous: int
    net_change_from_previous: int


class SnapshotTrendResponse(BaseModel):
    view_name: str
    compared_pairs: int
    points: list[SnapshotTrendPoint] = Field(default_factory=list)


class SnapshotTrendRequest(BaseModel):
    view_name: str
    limit: int = 5


class SnapshotTrendExportResponse(BaseModel):
    markdown: str
    json_path: str


class SnapshotUpdatePackRequest(BaseModel):
    view_name: str
    top_items: int = 5
    trend_limit: int = 8


class SnapshotUpdatePackResponse(BaseModel):
    view_name: str
    latest_diff_brief: SnapshotDiffBriefResponse
    trend: SnapshotTrendResponse


class SnapshotUpdatePackExportResponse(BaseModel):
    markdown: str
    json_path: str
