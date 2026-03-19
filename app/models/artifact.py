from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


ArtifactType = Literal["ask", "research", "batch_research"]


class ArtifactItem(BaseModel):
    id: str
    type: ArtifactType
    title: str
    template_name: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    markdown_path: Optional[str] = None
    json_path: Optional[str] = None
