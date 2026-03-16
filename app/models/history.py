from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class HistoryItem(BaseModel):
    type: Literal["ask", "research"]
    payload: dict[str, Any]


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]


class HistorySummary(BaseModel):
    id: str
    type: Literal["ask", "research"]
    created_at: datetime | None = None
    title: str
