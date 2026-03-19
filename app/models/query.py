from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    notebook_id: Optional[str] = None
    artifact_type: str = "summary"
    tags: List[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    notebook_id: str
    notebook_url: str
    question: str
    answer: str
    sources: List[str] = Field(default_factory=list)
    artifact_type: str = "summary"
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    output_markdown_path: Optional[str] = None
    output_json_path: Optional[str] = None
