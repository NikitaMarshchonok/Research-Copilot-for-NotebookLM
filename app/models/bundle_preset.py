from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

BundleArtifactType = Literal["ask", "research", "batch_research"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BundlePresetEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    item_types: list[BundleArtifactType] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class BundlePresetCreateRequest(BaseModel):
    name: str
    description: str = ""
    item_types: list[BundleArtifactType] = Field(min_length=1)
