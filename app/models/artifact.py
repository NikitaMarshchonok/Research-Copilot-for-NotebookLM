from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


ArtifactType = Literal["ask", "research", "batch_research"]


class ArtifactItem(BaseModel):
    id: str
    type: ArtifactType
    title: str
    created_at: Optional[datetime] = None
    markdown_path: Optional[str] = None
    json_path: Optional[str] = None
