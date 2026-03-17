from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TemplateEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    questions: list[str] = Field(default_factory=list, min_length=1)
    artifact_type: str = "study_guide"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class TemplateCreateRequest(BaseModel):
    name: str
    description: str = ""
    questions: list[str] = Field(min_length=1)
    artifact_type: str = "study_guide"


class RunTemplateRequest(BaseModel):
    topic: str = Field(min_length=3)
    template_name: str
    notebook_id: Optional[str] = None
    artifact_type: Optional[str] = None


class RunBatchTemplateRequest(BaseModel):
    topics: list[str] = Field(min_length=1)
    template_name: str
    notebook_id: Optional[str] = None
    artifact_type: Optional[str] = None
    continue_on_error: bool = True
