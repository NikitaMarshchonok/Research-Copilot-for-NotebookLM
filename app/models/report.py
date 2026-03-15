from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.query import AskResponse


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=3)
    questions: List[str] = Field(min_length=1)
    notebook_id: Optional[str] = None
    artifact_type: str = "study_guide"


class ResearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    notebook_id: str
    artifact_type: str
    items: List[AskResponse]
    created_at: datetime = Field(default_factory=utcnow)
    output_markdown_path: Optional[str] = None
    output_json_path: Optional[str] = None
