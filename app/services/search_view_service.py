from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.search_view import SearchViewCreateRequest, SearchViewEntry
from app.storage.json_store import JsonStore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SearchViewService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.store.ensure()

    def list_views(self) -> list[SearchViewEntry]:
        data = self.store.read()
        return [SearchViewEntry.model_validate(item) for item in data.get("items", [])]

    def add_view(self, payload: SearchViewCreateRequest) -> SearchViewEntry:
        data = self.store.read()
        items = data.get("items", [])
        normalized = payload.name.strip().lower()
        if any(str(item.get("name", "")).strip().lower() == normalized for item in items):
            raise ValidationAppError(f"Search view '{payload.name}' already exists.")
        view = SearchViewEntry(**payload.model_dump())
        items.append(view.model_dump(mode="json"))
        self.store.write({"items": items})
        return view

    def delete_view(self, name: str) -> None:
        normalized = name.strip().lower()
        data = self.store.read()
        items = data.get("items", [])
        filtered = [item for item in items if str(item.get("name", "")).strip().lower() != normalized]
        if len(filtered) == len(items):
            raise NotFoundError(f"Search view '{name}' not found.")
        self.store.write({"items": filtered})

    def get_view(self, name: str) -> SearchViewEntry:
        normalized = name.strip().lower()
        for view in self.list_views():
            if view.name.strip().lower() == normalized:
                return view
        raise NotFoundError(f"Search view '{name}' not found.")
