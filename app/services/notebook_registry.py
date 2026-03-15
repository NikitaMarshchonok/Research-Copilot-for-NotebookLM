from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.core.exceptions import NotFoundError
from app.models.notebook import (
    NotebookCreate,
    NotebookEntry,
    NotebookRegistryState,
)
from app.storage.json_store import JsonStore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotebookRegistryService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    def _read_state(self) -> NotebookRegistryState:
        raw = self.store.read()
        return NotebookRegistryState.model_validate(raw)

    def _write_state(self, state: NotebookRegistryState) -> None:
        self.store.write(state.model_dump(mode="json"))

    def list_notebooks(self) -> List[NotebookEntry]:
        return self._read_state().items

    def add_notebook(self, payload: NotebookCreate) -> NotebookEntry:
        state = self._read_state()
        notebook = NotebookEntry(**payload.model_dump())
        state.items.append(notebook)
        self._write_state(state)
        return notebook

    def select_active(self, notebook_id: str) -> NotebookEntry:
        state = self._read_state()
        notebook = next((n for n in state.items if n.id == notebook_id), None)
        if notebook is None:
            raise NotFoundError(f"Notebook with id '{notebook_id}' not found.")
        notebook.updated_at = utcnow()
        state.active_notebook_id = notebook_id
        self._write_state(state)
        return notebook

    def get_active(self) -> NotebookEntry:
        state = self._read_state()
        if not state.active_notebook_id:
            raise NotFoundError("No active notebook selected.")
        notebook = next((n for n in state.items if n.id == state.active_notebook_id), None)
        if notebook is None:
            raise NotFoundError("Active notebook id points to missing notebook.")
        return notebook
