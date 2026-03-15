from __future__ import annotations

import json
from typing import List, Optional

import typer

from app.bootstrap import build_container
from app.core.logger import setup_logging
from app.models.notebook import NotebookCreate
from app.models.query import AskRequest
from app.models.report import ResearchRequest

app = typer.Typer(help="Research Copilot CLI")
notebooks_app = typer.Typer(help="Notebook registry commands")
app.add_typer(notebooks_app, name="notebooks")


def _container():
    container = build_container()
    setup_logging(container.settings.log_level)
    return container


@app.command("init")
def init_project() -> None:
    container = _container()
    container.notebooks_store.ensure()
    container.history_store.ensure()
    container.settings.outputs_path.mkdir(parents=True, exist_ok=True)
    typer.echo("Initialized data/ and outputs/ directories.")


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


@app.command("export")
def export(
    history_id: str = typer.Option(..., "--history-id"),
) -> None:
    container = _container()
    paths = container.research_service.export_from_history(history_id)
    typer.echo(json.dumps(paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
