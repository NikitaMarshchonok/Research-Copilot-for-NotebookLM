from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.workspace import (
    WorkspaceContext,
    WorkspaceCreateRequest,
    WorkspaceCurrentResponse,
    WorkspaceEntry,
    WorkspaceRegistryState,
)
from app.storage.json_store import JsonStore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceService:
    def __init__(self, settings: Settings, registry_store: JsonStore) -> None:
        self.settings = settings
        self.registry_store = registry_store
        self.registry_store.ensure()
        Path(self.settings.workspaces_path).mkdir(parents=True, exist_ok=True)
        self._ensure_default_workspace()

    def _ensure_default_workspace(self) -> None:
        state = self._read_state()
        if any(item.name.strip().lower() == "default" for item in state.items):
            return
        state.items.append(
            WorkspaceEntry(
                name="default",
                description="Default local workspace",
            )
        )
        self._write_state(state)

    def _read_state(self) -> WorkspaceRegistryState:
        return WorkspaceRegistryState.model_validate(self.registry_store.read())

    def _write_state(self, state: WorkspaceRegistryState) -> None:
        self.registry_store.write(state.model_dump(mode="json"))

    def list_workspaces(self) -> list[WorkspaceEntry]:
        return self._read_state().items

    def create_workspace(self, payload: WorkspaceCreateRequest) -> WorkspaceEntry:
        state = self._read_state()
        normalized = payload.name.strip().lower()
        if not normalized:
            raise ValidationAppError("Workspace name cannot be empty.")
        if any(item.name.strip().lower() == normalized for item in state.items):
            raise ValidationAppError(f"Workspace '{payload.name}' already exists.")
        workspace = WorkspaceEntry(name=payload.name.strip(), description=payload.description)
        state.items.append(workspace)
        self._write_state(state)
        self._ensure_workspace_paths(workspace.name)
        return workspace

    def select_workspace(self, workspace_name: str) -> WorkspaceEntry:
        state = self._read_state()
        target = next(
            (item for item in state.items if item.name.strip().lower() == workspace_name.strip().lower()),
            None,
        )
        if target is None:
            raise NotFoundError(f"Workspace '{workspace_name}' not found.")
        state.active_workspace = target.name
        target.updated_at = utcnow()
        self._write_state(state)
        self._ensure_workspace_paths(target.name)
        return target

    def get_active_workspace_entry(self) -> WorkspaceEntry:
        state = self._read_state()
        target = next(
            (item for item in state.items if item.name.strip().lower() == state.active_workspace.strip().lower()),
            None,
        )
        if target is None:
            raise NotFoundError(f"Active workspace '{state.active_workspace}' not found.")
        return target

    def get_active_context(self) -> WorkspaceContext:
        entry = self.get_active_workspace_entry()
        data_path, outputs_path = self._workspace_paths(entry.name)
        self._ensure_workspace_paths(entry.name)
        return WorkspaceContext(name=entry.name, data_path=data_path, outputs_path=outputs_path)

    def get_current_response(self) -> WorkspaceCurrentResponse:
        entry = self.get_active_workspace_entry()
        context = self.get_active_context()
        return WorkspaceCurrentResponse(
            active_workspace=entry.name,
            data_path=str(context.data_path),
            outputs_path=str(context.outputs_path),
            workspace=entry,
        )

    def _workspace_paths(self, workspace_name: str) -> tuple:
        normalized = workspace_name.strip().lower()
        if normalized == "default":
            return self.settings.data_path, self.settings.outputs_path
        workspace_root = self.settings.workspaces_path / workspace_name
        return workspace_root / "data", workspace_root / "outputs"

    def _ensure_workspace_paths(self, workspace_name: str) -> None:
        data_path, outputs_path = self._workspace_paths(workspace_name)
        data_path.mkdir(parents=True, exist_ok=True)
        outputs_path.mkdir(parents=True, exist_ok=True)
