from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    type: Literal["ask", "research", "batch_research"]
    payload: dict[str, Any]


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]


class HistorySummary(BaseModel):
    id: str
    type: Literal["ask", "research", "batch_research"]
    created_at: datetime | None = None
    title: str
    tags: list[str] = Field(default_factory=list)
