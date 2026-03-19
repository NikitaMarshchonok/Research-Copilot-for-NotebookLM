from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class ExportRequest(BaseModel):
    history_id: str


class ExportResponse(BaseModel):
    markdown: str
    json_path: str


class LatestExportRequest(BaseModel):
    item_type: str | None = None
    template_name: str | None = None
    tag: str | None = None
    query: str | None = None


class BundleExportRequest(BaseModel):
    bundle_name: str = "article-pack"
    template_name: Optional[str] = None


class BundleExportResponse(BaseModel):
    markdown: str
    json_path: str
    included_count: int
