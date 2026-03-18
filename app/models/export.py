from __future__ import annotations

from pydantic import BaseModel


class ExportRequest(BaseModel):
    history_id: str


class ExportResponse(BaseModel):
    markdown: str
    json_path: str


class LatestExportRequest(BaseModel):
    item_type: str | None = None
    template_name: str | None = None
