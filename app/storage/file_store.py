from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "report"


class FileStore:
    def __init__(self, outputs_path: Path) -> None:
        self.outputs_path = outputs_path
        self.outputs_path.mkdir(parents=True, exist_ok=True)

    def save_markdown(self, title: str, content: str, prefix: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{prefix}-{_slugify(title)}-{timestamp}.md"
        file_path = self.outputs_path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def save_json(self, title: str, payload: Any, prefix: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{prefix}-{_slugify(title)}-{timestamp}.json"
        file_path = self.outputs_path / filename
        file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return file_path
