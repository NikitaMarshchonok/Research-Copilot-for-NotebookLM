from __future__ import annotations

import json
from typing import List, Optional

import typer

from app.core.exceptions import NotFoundError
from app.bootstrap import build_container
from app.core.logger import setup_logging
from app.models.notebook import NotebookCreate
from app.models.bundle_preset import BundlePresetCreateRequest
from app.models.query import AskRequest
from app.models.report import ResearchRequest
from app.models.search_view import SearchViewCreateRequest
from app.models.snapshot import SnapshotCreateRequest
from app.models.template import TemplateCreateRequest
from app.models.workspace import WorkspaceCreateRequest

app = typer.Typer(help="Research Copilot CLI")
notebooks_app = typer.Typer(help="Notebook registry commands")
history_app = typer.Typer(help="History commands")
artifacts_app = typer.Typer(help="Artifacts index commands")
bundles_app = typer.Typer(help="Bundle preset commands")
views_app = typer.Typer(help="Saved search view commands")
snapshots_app = typer.Typer(help="Snapshot commands")
templates_app = typer.Typer(help="Template commands")
workspaces_app = typer.Typer(help="Workspace commands")
app.add_typer(notebooks_app, name="notebooks")
app.add_typer(history_app, name="history")
app.add_typer(artifacts_app, name="artifacts")
app.add_typer(bundles_app, name="bundles")
app.add_typer(views_app, name="views")
app.add_typer(snapshots_app, name="snapshots")
app.add_typer(templates_app, name="templates")
app.add_typer(workspaces_app, name="workspaces")


def _container():
    container = build_container()
    setup_logging(container.settings.log_level)
    return container


@app.command("init")
def init_project() -> None:
    container = _container()
    container.workspace_service.get_active_context()
    container.notebooks_store.ensure()
    container.history_store.ensure()
    container.templates_store.ensure()
    container.bundle_presets_store.ensure()
    container.search_views_store.ensure()
    container.snapshots_store.ensure()
    typer.echo(
        f"Initialized workspace '{container.active_workspace}' "
        "(notebooks, history, templates, bundle presets, search views, snapshots, outputs)."
    )


@notebooks_app.command("list")
def notebooks_list() -> None:
    container = _container()
    notebooks = container.notebook_registry.list_notebooks()
    if not notebooks:
        typer.echo("No notebooks found.")
        return
    for notebook in notebooks:
        typer.echo(f"{notebook.id} | {notebook.name} | {notebook.url}")


@notebooks_app.command("add")
def notebooks_add(
    name: str = typer.Option(..., "--name"),
    url: str = typer.Option(..., "--url"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags."),
    description: str = typer.Option("", "--description"),
) -> None:
    container = _container()
    notebook = container.notebook_registry.add_notebook(
        NotebookCreate(
            name=name,
            url=url,
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
            description=description,
        )
    )
    typer.echo(f"Added notebook: {notebook.id}")


@notebooks_app.command("select")
def notebooks_select(notebook_id: str = typer.Argument(...)) -> None:
    container = _container()
    notebook = container.notebook_registry.select_active(notebook_id)
    typer.echo(f"Active notebook set: {notebook.id} ({notebook.name})")


@notebooks_app.command("active")
def notebooks_active() -> None:
    container = _container()
    try:
        notebook = container.notebook_registry.get_active()
        typer.echo(f"{notebook.id} | {notebook.name} | {notebook.url}")
    except NotFoundError as exc:
        typer.echo(str(exc))


@app.command("ask")
def ask(
    question: str = typer.Option(..., "--question"),
    notebook_id: Optional[str] = typer.Option(None, "--notebook-id"),
    artifact_type: str = typer.Option("summary", "--artifact-type"),
    tags: List[str] = typer.Option([], "--tag"),
) -> None:
    container = _container()
    response = container.research_service.ask(
        AskRequest(
            question=question,
            notebook_id=notebook_id,
            artifact_type=artifact_type,
            tags=tags,
        )
    )
    typer.echo(response.answer)
    typer.echo(f"Saved markdown: {response.output_markdown_path}")
    typer.echo(f"Saved json: {response.output_json_path}")


@app.command("research")
def research(
    topic: str = typer.Option(..., "--topic"),
    questions: List[str] = typer.Option(..., "--question"),
    notebook_id: Optional[str] = typer.Option(None, "--notebook-id"),
    artifact_type: str = typer.Option("study_guide", "--artifact-type"),
    tags: List[str] = typer.Option([], "--tag"),
) -> None:
    container = _container()
    response = container.research_service.research(
        ResearchRequest(
            topic=topic,
            questions=questions,
            notebook_id=notebook_id,
            artifact_type=artifact_type,
            tags=tags,
        )
    )
    typer.echo(f"Research report generated: {response.id}")
    typer.echo(f"Saved markdown: {response.output_markdown_path}")
    typer.echo(f"Saved json: {response.output_json_path}")


@app.command("research-template")
def research_template(
    topic: str = typer.Option(..., "--topic"),
    template_name: str = typer.Option(..., "--template"),
    notebook_id: Optional[str] = typer.Option(None, "--notebook-id"),
    artifact_type: Optional[str] = typer.Option(None, "--artifact-type"),
    tags: List[str] = typer.Option([], "--tag"),
) -> None:
    container = _container()
    response = container.research_service.research_from_template(
        topic=topic,
        template_name=template_name,
        notebook_id=notebook_id,
        artifact_type=artifact_type,
        tags=tags,
    )
    typer.echo(f"Research report generated from template: {response.id}")
    typer.echo(f"Saved markdown: {response.output_markdown_path}")
    typer.echo(f"Saved json: {response.output_json_path}")


@app.command("research-batch-template")
def research_batch_template(
    topics: List[str] = typer.Option(..., "--topic"),
    template_name: str = typer.Option(..., "--template"),
    notebook_id: Optional[str] = typer.Option(None, "--notebook-id"),
    artifact_type: Optional[str] = typer.Option(None, "--artifact-type"),
    tags: List[str] = typer.Option([], "--tag"),
    continue_on_error: bool = typer.Option(True, "--continue-on-error/--fail-fast"),
) -> None:
    container = _container()
    response = container.research_service.batch_research_from_template(
        topics=topics,
        template_name=template_name,
        notebook_id=notebook_id,
        artifact_type=artifact_type,
        tags=tags,
        continue_on_error=continue_on_error,
    )
    typer.echo(f"Batch research generated: {response.id}")
    typer.echo(f"Completed topics: {len(response.items)}")
    typer.echo(f"Failed topics: {len(response.failures)}")
    typer.echo(f"Saved markdown: {response.output_markdown_path}")
    typer.echo(f"Saved json: {response.output_json_path}")


@app.command("export")
def export(
    history_id: str = typer.Option(..., "--history-id"),
) -> None:
    container = _container()
    paths = container.research_service.export_from_history(history_id)
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


@app.command("export-latest")
def export_latest(
    item_type: Optional[str] = typer.Option(
        None, "--type", help="Filter by: ask, research, batch_research"
    ),
    template_name: Optional[str] = typer.Option(None, "--template"),
    tag: Optional[str] = typer.Option(None, "--tag"),
    query: Optional[str] = typer.Option(None, "--query"),
) -> None:
    container = _container()
    paths = container.research_service.export_latest_artifact(
        item_type=item_type,
        template_name=template_name,
        tag=tag,
        query=query,
    )
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


@app.command("export-bundle")
def export_bundle(
    bundle_name: str = typer.Option("article-pack", "--name"),
    template_name: Optional[str] = typer.Option(None, "--template"),
) -> None:
    container = _container()
    paths = container.research_service.export_artifact_bundle(
        bundle_name=bundle_name,
        template_name=template_name,
    )
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


@bundles_app.command("list")
def bundles_list() -> None:
    container = _container()
    presets = container.research_service.list_bundle_presets()
    for preset in presets:
        typer.echo(
            f"{preset.name} | types={','.join(preset.item_types)} | {preset.description}"
        )


@bundles_app.command("add")
def bundles_add(
    name: str = typer.Option(..., "--name"),
    item_types: List[str] = typer.Option(..., "--type"),
    description: str = typer.Option("", "--description"),
) -> None:
    container = _container()
    preset = container.research_service.add_bundle_preset(
        BundlePresetCreateRequest(
            name=name,
            item_types=item_types,  # type: ignore[arg-type]
            description=description,
        )
    )
    typer.echo(f"Bundle preset added: {preset.name}")


@bundles_app.command("delete")
def bundles_delete(name: str = typer.Option(..., "--name")) -> None:
    container = _container()
    container.research_service.delete_bundle_preset(name)
    typer.echo(f"Bundle preset deleted: {name}")


@views_app.command("list")
def views_list() -> None:
    container = _container()
    for view in container.research_service.list_search_views():
        typer.echo(
            f"{view.name} | scope={view.scope} | type={view.item_type} | "
            f"template={view.template_name} | tag={view.tag} | query={view.query}"
        )


@views_app.command("add")
def views_add(
    name: str = typer.Option(..., "--name"),
    scope: str = typer.Option(..., "--scope", help="history|artifacts"),
    item_type: Optional[str] = typer.Option(None, "--type"),
    template_name: Optional[str] = typer.Option(None, "--template"),
    tag: Optional[str] = typer.Option(None, "--tag"),
    query: Optional[str] = typer.Option(None, "--query"),
    description: str = typer.Option("", "--description"),
) -> None:
    container = _container()
    view = container.research_service.add_search_view(
        SearchViewCreateRequest(
            name=name,
            scope=scope,  # type: ignore[arg-type]
            item_type=item_type,
            template_name=template_name,
            tag=tag,
            query=query,
            description=description,
        )
    )
    typer.echo(f"Search view added: {view.name}")


@views_app.command("run")
def views_run(name: str = typer.Option(..., "--name")) -> None:
    container = _container()
    result = container.research_service.run_search_view(name)
    typer.echo(result.model_dump_json(indent=2))


@views_app.command("delete")
def views_delete(name: str = typer.Option(..., "--name")) -> None:
    container = _container()
    container.research_service.delete_search_view(name)
    typer.echo(f"Search view deleted: {name}")


@snapshots_app.command("create")
def snapshots_create(view_name: str = typer.Option(..., "--view")) -> None:
    container = _container()
    snapshot = container.research_service.create_snapshot(
        SnapshotCreateRequest(view_name=view_name)
    )
    typer.echo(
        f"Snapshot created: {snapshot.id} | view={snapshot.view_name} | items={snapshot.item_count}"
    )


@snapshots_app.command("list")
def snapshots_list(view_name: Optional[str] = typer.Option(None, "--view")) -> None:
    container = _container()
    snapshots = container.research_service.list_snapshots(view_name=view_name)
    if not snapshots:
        typer.echo("No snapshots found.")
        return
    for snapshot in snapshots:
        typer.echo(
            f"{snapshot.id} | view={snapshot.view_name} | items={snapshot.item_count} | "
            f"md={snapshot.output_markdown_path}"
        )


@snapshots_app.command("get")
def snapshots_get(snapshot_id: str = typer.Option(..., "--id")) -> None:
    container = _container()
    snapshot = container.research_service.get_snapshot(snapshot_id)
    typer.echo(snapshot.model_dump_json(indent=2))


@snapshots_app.command("diff")
def snapshots_diff(
    from_snapshot_id: str = typer.Option(..., "--from"),
    to_snapshot_id: str = typer.Option(..., "--to"),
) -> None:
    container = _container()
    diff = container.research_service.diff_snapshots(
        from_snapshot_id=from_snapshot_id,
        to_snapshot_id=to_snapshot_id,
    )
    typer.echo(diff.model_dump_json(indent=2))


@snapshots_app.command("diff-export")
def snapshots_diff_export(
    from_snapshot_id: str = typer.Option(..., "--from"),
    to_snapshot_id: str = typer.Option(..., "--to"),
) -> None:
    container = _container()
    paths = container.research_service.export_snapshot_diff(
        from_snapshot_id=from_snapshot_id,
        to_snapshot_id=to_snapshot_id,
    )
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


@snapshots_app.command("diff-latest")
def snapshots_diff_latest(view_name: str = typer.Option(..., "--view")) -> None:
    container = _container()
    diff = container.research_service.diff_latest_snapshots(view_name=view_name)
    typer.echo(diff.model_dump_json(indent=2))


@snapshots_app.command("diff-latest-export")
def snapshots_diff_latest_export(view_name: str = typer.Option(..., "--view")) -> None:
    container = _container()
    paths = container.research_service.export_latest_snapshot_diff(view_name=view_name)
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


@history_app.command("list")
def history_list(
    item_type: Optional[str] = typer.Option(
        None, "--type", help="Filter by: ask, research, batch_research"
    ),
    tag: Optional[str] = typer.Option(None, "--tag"),
    query: Optional[str] = typer.Option(None, "--query"),
) -> None:
    container = _container()
    items = container.research_service.list_history(
        item_type=item_type,
        tag=tag,
        query=query,
    )
    if not items:
        typer.echo("History is empty.")
        return
    for item in items:
        typer.echo(
            f"{item.id} | {item.type} | {item.title} | tags={','.join(item.tags)} | {item.created_at}"
        )


@history_app.command("get")
def history_get(history_id: str = typer.Argument(...)) -> None:
    container = _container()
    item = container.research_service.get_history_item(history_id)
    typer.echo(item.model_dump_json(indent=2))


@artifacts_app.command("list")
def artifacts_list(
    item_type: Optional[str] = typer.Option(
        None, "--type", help="Filter by: ask, research, batch_research"
    ),
    template_name: Optional[str] = typer.Option(None, "--template"),
    tag: Optional[str] = typer.Option(None, "--tag"),
    query: Optional[str] = typer.Option(None, "--query"),
) -> None:
    container = _container()
    items = container.research_service.list_artifacts(
        item_type=item_type,
        template_name=template_name,
        tag=tag,
        query=query,
    )
    if not items:
        typer.echo("No artifacts found.")
        return
    for item in items:
        typer.echo(
            f"{item.id} | {item.type} | {item.title} | tags={','.join(item.tags)} | "
            f"md={item.markdown_path} | json={item.json_path}"
        )


@artifacts_app.command("latest")
def artifacts_latest(
    item_type: Optional[str] = typer.Option(
        None, "--type", help="Filter by: ask, research, batch_research"
    ),
    template_name: Optional[str] = typer.Option(None, "--template"),
    tag: Optional[str] = typer.Option(None, "--tag"),
    query: Optional[str] = typer.Option(None, "--query"),
) -> None:
    container = _container()
    item = container.research_service.get_latest_artifact(
        item_type=item_type,
        template_name=template_name,
        tag=tag,
        query=query,
    )
    typer.echo(
        f"{item.id} | {item.type} | {item.title} | template={item.template_name} | "
        f"tags={','.join(item.tags)} | md={item.markdown_path} | json={item.json_path}"
    )


@templates_app.command("list")
def templates_list() -> None:
    container = _container()
    templates = container.template_service.list_templates()
    if not templates:
        typer.echo("No templates found.")
        return
    for template in templates:
        typer.echo(
            f"{template.id} | {template.name} | {template.artifact_type} | questions={len(template.questions)}"
        )


@templates_app.command("add")
def templates_add(
    name: str = typer.Option(..., "--name"),
    questions: List[str] = typer.Option(..., "--question"),
    description: str = typer.Option("", "--description"),
    artifact_type: str = typer.Option("study_guide", "--artifact-type"),
) -> None:
    container = _container()
    template = container.template_service.add_template(
        TemplateCreateRequest(
            name=name,
            questions=questions,
            description=description,
            artifact_type=artifact_type,
        )
    )
    typer.echo(f"Template added: {template.id} ({template.name})")


@workspaces_app.command("list")
def workspaces_list() -> None:
    container = _container()
    current = container.workspace_service.get_current_response().active_workspace
    for workspace in container.workspace_service.list_workspaces():
        marker = "*" if workspace.name == current else " "
        typer.echo(f"{marker} {workspace.name} | {workspace.description}")


@workspaces_app.command("create")
def workspaces_create(
    name: str = typer.Option(..., "--name"),
    description: str = typer.Option("", "--description"),
) -> None:
    container = _container()
    workspace = container.workspace_service.create_workspace(
        WorkspaceCreateRequest(name=name, description=description)
    )
    typer.echo(f"Workspace created: {workspace.name}")


@workspaces_app.command("select")
def workspaces_select(name: str = typer.Option(..., "--name")) -> None:
    container = _container()
    workspace = container.workspace_service.select_workspace(name)
    typer.echo(f"Active workspace set: {workspace.name}")


@workspaces_app.command("current")
def workspaces_current() -> None:
    container = _container()
    current = container.workspace_service.get_current_response()
    typer.echo(current.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
