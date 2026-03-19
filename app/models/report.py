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
    tags: List[str] = Field(default_factory=list)


class ResearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    notebook_id: str
    artifact_type: str
    tags: List[str] = Field(default_factory=list)
    items: List[AskResponse]
    created_at: datetime = Field(default_factory=utcnow)
    output_markdown_path: Optional[str] = None
    output_json_path: Optional[str] = None


class BatchResearchTemplateRequest(BaseModel):
    topics: List[str] = Field(min_length=1)
    template_name: str
    notebook_id: Optional[str] = None
    artifact_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    continue_on_error: bool = True


class BatchResearchFailure(BaseModel):
    topic: str
    error: str


class BatchResearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    template_name: str
    notebook_id: Optional[str] = None
    artifact_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    items: List[ResearchResponse] = Field(default_factory=list)
    failures: List[BatchResearchFailure] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    output_markdown_path: Optional[str] = None
    output_json_path: Optional[str] = None
