from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.exceptions import IntegrationError
from app.models.notebook import NotebookRegistryState
from app.services.export_service import ExportService
from app.services.notebook_registry import NotebookRegistryService
from app.services.notebooklm_client import BridgeNotebookLMClient, NotebookLMClient, StubNotebookLMClient
from app.services.research_service import ResearchService
from app.services.template_service import TemplateService
from app.services.workspace_service import WorkspaceService
from app.storage.file_store import FileStore
from app.storage.json_store import JsonStore


@dataclass
class ServiceContainer:
    settings: Settings
    workspace_service: WorkspaceService
    active_workspace: str
    notebooks_store: JsonStore
    history_store: JsonStore
    templates_store: JsonStore
    notebook_registry: NotebookRegistryService
    template_service: TemplateService
    research_service: ResearchService


def _build_notebooklm_client(settings: Settings) -> NotebookLMClient:
    if settings.notebooklm_connector_mode.lower() == "bridge":
        try:
            return BridgeNotebookLMClient(command=settings.notebooklm_bridge_command)
        except IntegrationError:
            return StubNotebookLMClient()
    return StubNotebookLMClient()


def build_container() -> ServiceContainer:
    settings = get_settings()
    workspace_registry_store = JsonStore(
        settings.data_path / "workspaces.json",
        default_value={"active_workspace": "default", "items": []},
    )
    workspace_service = WorkspaceService(settings=settings, registry_store=workspace_registry_store)
    workspace_context = workspace_service.get_active_context()

    notebooks_store = JsonStore(
        workspace_context.data_path / "notebooks.json",
        default_value=NotebookRegistryState().model_dump(mode="json"),
    )
    history_store = JsonStore(workspace_context.data_path / "history.json", default_value={"items": []})
    templates_store = JsonStore(workspace_context.data_path / "templates.json", default_value={"items": []})

    notebook_registry = NotebookRegistryService(notebooks_store)
    template_service = TemplateService(templates_store)
    export_service = ExportService(FileStore(workspace_context.outputs_path))
    research_service = ResearchService(
        registry=notebook_registry,
        template_service=template_service,
        notebooklm_client=_build_notebooklm_client(settings),
        export_service=export_service,
        history_store=history_store,
    )

    return ServiceContainer(
        settings=settings,
        workspace_service=workspace_service,
        active_workspace=workspace_context.name,
        notebooks_store=notebooks_store,
        history_store=history_store,
        templates_store=templates_store,
        notebook_registry=notebook_registry,
        template_service=template_service,
        research_service=research_service,
    )
