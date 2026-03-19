from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SearchScope = Literal["history", "artifacts"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SearchViewEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    scope: SearchScope
    item_type: str | None = None
    template_name: str | None = None
    tag: str | None = None
    query: str | None = None
    description: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SearchViewCreateRequest(BaseModel):
    name: str
    scope: SearchScope
    item_type: str | None = None
    template_name: str | None = None
    tag: str | None = None
    query: str | None = None
    description: str = ""


class SearchViewRunResponse(BaseModel):
    name: str
    scope: SearchScope
    item_count: int
    items: list[dict[str, Any]]
