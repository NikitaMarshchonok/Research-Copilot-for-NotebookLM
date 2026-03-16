from __future__ import annotations

import json
from typing import List, Optional

import typer

from app.core.exceptions import NotFoundError
from app.bootstrap import build_container
from app.core.logger import setup_logging
from app.models.notebook import NotebookCreate
from app.models.query import AskRequest
from app.models.report import ResearchRequest
from app.models.template import TemplateCreateRequest

app = typer.Typer(help="Research Copilot CLI")
notebooks_app = typer.Typer(help="Notebook registry commands")
history_app = typer.Typer(help="History commands")
templates_app = typer.Typer(help="Template commands")
app.add_typer(notebooks_app, name="notebooks")
app.add_typer(history_app, name="history")
app.add_typer(templates_app, name="templates")


def _container():
    container = build_container()
    setup_logging(container.settings.log_level)
    return container


@app.command("init")
def init_project() -> None:
    container = _container()
    container.notebooks_store.ensure()
    container.history_store.ensure()
    container.templates_store.ensure()
    container.settings.outputs_path.mkdir(parents=True, exist_ok=True)
    typer.echo("Initialized data/ and outputs/ directories (notebooks, history, templates).")


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
) -> None:
    container = _container()
    response = container.research_service.ask(
        AskRequest(
            question=question,
            notebook_id=notebook_id,
            artifact_type=artifact_type,
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
) -> None:
    container = _container()
    response = container.research_service.research(
        ResearchRequest(
            topic=topic,
            questions=questions,
            notebook_id=notebook_id,
            artifact_type=artifact_type,
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
) -> None:
    container = _container()
    response = container.research_service.research_from_template(
        topic=topic,
        template_name=template_name,
        notebook_id=notebook_id,
        artifact_type=artifact_type,
    )
    typer.echo(f"Research report generated from template: {response.id}")
    typer.echo(f"Saved markdown: {response.output_markdown_path}")
    typer.echo(f"Saved json: {response.output_json_path}")


@app.command("export")
def export(
    history_id: str = typer.Option(..., "--history-id"),
) -> None:
    container = _container()
    paths = container.research_service.export_from_history(history_id)
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


@history_app.command("list")
def history_list() -> None:
    container = _container()
    items = container.research_service.list_history()
    if not items:
        typer.echo("History is empty.")
        return
    for item in items:
        typer.echo(f"{item.id} | {item.type} | {item.title} | {item.created_at}")


@history_app.command("get")
def history_get(history_id: str = typer.Argument(...)) -> None:
    container = _container()
    item = container.research_service.get_history_item(history_id)
    typer.echo(item.model_dump_json(indent=2))


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


if __name__ == "__main__":
    app()
