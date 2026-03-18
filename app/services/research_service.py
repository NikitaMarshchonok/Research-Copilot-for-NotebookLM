from __future__ import annotations

import logging
from typing import List

from app.core.exceptions import NotFoundError
from app.models.artifact import ArtifactItem
from app.models.history import HistoryItem, HistorySummary
from app.models.query import AskRequest, AskResponse
from app.models.report import (
    BatchResearchFailure,
    BatchResearchResponse,
    ResearchRequest,
    ResearchResponse,
)
from app.services.export_service import ExportService
from app.services.notebook_registry import NotebookRegistryService
from app.services.notebooklm_client import NotebookLMClient
from app.services.prompt_templates import build_question
from app.services.template_service import TemplateService
from app.storage.json_store import JsonStore

logger = logging.getLogger(__name__)

BUNDLE_PRESETS: dict[str, list[str]] = {
    "article-pack": ["research", "ask", "batch_research"],
    "tech-brief-pack": ["research", "batch_research"],
    "study-pack": ["research", "ask"],
}


class ResearchService:
    def __init__(
        self,
        registry: NotebookRegistryService,
        template_service: TemplateService,
        notebooklm_client: NotebookLMClient,
        export_service: ExportService,
        history_store: JsonStore,
    ) -> None:
        self.registry = registry
        self.template_service = template_service
        self.notebooklm_client = notebooklm_client
        self.export_service = export_service
        self.history_store = history_store
        self.history_store.ensure()

    def ask(self, request: AskRequest, save_outputs: bool = True) -> AskResponse:
        notebook = self.registry.select_active(request.notebook_id) if request.notebook_id else self.registry.get_active()
        compiled_question = build_question(request.question, request.artifact_type)
        answer = self.notebooklm_client.ask(str(notebook.url), compiled_question)

        response = AskResponse(
            notebook_id=notebook.id,
            notebook_url=str(notebook.url),
            question=request.question,
            answer=answer.answer,
            sources=answer.sources,
            artifact_type=request.artifact_type,
        )
        if save_outputs:
            response = self.export_service.export_answer(response)
        self._append_history({"type": "ask", "payload": response.model_dump(mode="json")})
        logger.info("Ask completed for notebook_id=%s", notebook.id)
        return response

    def research(self, request: ResearchRequest, save_outputs: bool = True) -> ResearchResponse:
        items: List[AskResponse] = []
        for question in request.questions:
            ask_result = self.ask(
                AskRequest(
                    question=question,
                    notebook_id=request.notebook_id,
                    artifact_type=request.artifact_type,
                ),
                save_outputs=False,
            )
            items.append(ask_result)

        notebook = self.registry.select_active(request.notebook_id) if request.notebook_id else self.registry.get_active()
        response = ResearchResponse(
            topic=request.topic,
            notebook_id=notebook.id,
            artifact_type=request.artifact_type,
            items=items,
        )
        if save_outputs:
            response = self.export_service.export_research(response)
        self._append_history({"type": "research", "payload": response.model_dump(mode="json")})
        logger.info("Research completed for topic='%s'", request.topic)
        return response

    def export_from_history(self, item_id: str) -> dict[str, str]:
        matched = self.get_history_item(item_id).model_dump(mode="json")

        payload = matched["payload"]
        if matched["type"] == "ask":
            response = AskResponse.model_validate(payload)
            response = self.export_service.export_answer(response)
            return {
                "markdown": response.output_markdown_path or "",
                "json": response.output_json_path or "",
            }

        if matched["type"] == "research":
            response = ResearchResponse.model_validate(payload)
            response = self.export_service.export_research(response)
            return {
                "markdown": response.output_markdown_path or "",
                "json": response.output_json_path or "",
            }

        batch_response = BatchResearchResponse.model_validate(payload)
        batch_response = self.export_service.export_batch_research(batch_response)
        return {
            "markdown": batch_response.output_markdown_path or "",
            "json": batch_response.output_json_path or "",
        }

    def research_from_template(
        self,
        topic: str,
        template_name: str,
        notebook_id: str | None = None,
        artifact_type: str | None = None,
    ) -> ResearchResponse:
        questions, template_artifact = self.template_service.render_questions(template_name, topic)
        return self.research(
            ResearchRequest(
                topic=topic,
                questions=questions,
                notebook_id=notebook_id,
                artifact_type=artifact_type or template_artifact,
            )
        )

    def batch_research_from_template(
        self,
        topics: list[str],
        template_name: str,
        notebook_id: str | None = None,
        artifact_type: str | None = None,
        continue_on_error: bool = True,
    ) -> BatchResearchResponse:
        items: list[ResearchResponse] = []
        failures: list[BatchResearchFailure] = []

        for topic in topics:
            try:
                report = self.research_from_template(
                    topic=topic,
                    template_name=template_name,
                    notebook_id=notebook_id,
                    artifact_type=artifact_type,
                )
                items.append(report)
            except Exception as exc:  # noqa: BLE001
                failures.append(BatchResearchFailure(topic=topic, error=str(exc)))
                if not continue_on_error:
                    break

        response = BatchResearchResponse(
            template_name=template_name,
            notebook_id=notebook_id,
            artifact_type=artifact_type,
            items=items,
            failures=failures,
        )
        response = self.export_service.export_batch_research(response)
        self._append_history({"type": "batch_research", "payload": response.model_dump(mode="json")})
        return response

    def list_history(self) -> list[HistorySummary]:
        history = self.history_store.read()
        summaries: list[HistorySummary] = []
        for entry in history.get("items", []):
            payload = entry.get("payload", {})
            item_type = entry.get("type", "ask")
            title = (
                payload.get("question")
                or payload.get("topic")
                or payload.get("template_name")
                or "Untitled history item"
            )
            summaries.append(
                HistorySummary(
                    id=str(payload.get("id", "")),
                    type=item_type,
                    created_at=payload.get("created_at"),
                    title=title,
                )
            )
        return summaries

    def list_artifacts(
        self, item_type: str | None = None, template_name: str | None = None
    ) -> list[ArtifactItem]:
        history = self.history_store.read()
        artifacts: list[ArtifactItem] = []
        for entry in history.get("items", []):
            entry_type = str(entry.get("type", "ask"))
            if item_type and entry_type != item_type:
                continue
            payload = entry.get("payload", {})
            payload_template = payload.get("template_name")
            if template_name and str(payload_template or "").strip().lower() != template_name.strip().lower():
                continue
            title = (
                payload.get("question")
                or payload.get("topic")
                or payload.get("template_name")
                or "Untitled artifact"
            )
            artifacts.append(
                ArtifactItem(
                    id=str(payload.get("id", "")),
                    type=entry_type,  # type: ignore[arg-type]
                    title=str(title),
                    template_name=str(payload_template) if payload_template else None,
                    created_at=payload.get("created_at"),
                    markdown_path=payload.get("output_markdown_path"),
                    json_path=payload.get("output_json_path"),
                )
            )
        artifacts.sort(
            key=lambda item: item.created_at.isoformat() if item.created_at else "",
            reverse=True,
        )
        return artifacts

    def get_latest_artifact(
        self, item_type: str | None = None, template_name: str | None = None
    ) -> ArtifactItem:
        artifacts = self.list_artifacts(item_type=item_type, template_name=template_name)
        if not artifacts:
            raise NotFoundError("No artifacts found for the provided filter.")
        return artifacts[0]

    def export_latest_artifact(
        self, item_type: str | None = None, template_name: str | None = None
    ) -> dict[str, str]:
        latest = self.get_latest_artifact(item_type=item_type, template_name=template_name)
        return self.export_from_history(latest.id)

    def export_artifact_bundle(
        self, bundle_name: str = "article-pack", template_name: str | None = None
    ) -> dict[str, str | int]:
        filters = BUNDLE_PRESETS.get(bundle_name, BUNDLE_PRESETS["article-pack"])
        selected: list[ArtifactItem] = []
        seen_ids: set[str] = set()
        for item_type in filters:
            artifacts = self.list_artifacts(item_type=item_type, template_name=template_name)
            if not artifacts:
                continue
            latest = artifacts[0]
            if latest.id in seen_ids:
                continue
            selected.append(latest)
            seen_ids.add(latest.id)

        if not selected:
            raise NotFoundError("No artifacts available for selected bundle filter.")

        paths = self.export_service.export_artifact_bundle(bundle_name=bundle_name, items=selected)
        return {
            "markdown": paths["markdown"],
            "json": paths["json"],
            "included_count": len(selected),
        }

    def get_history_item(self, item_id: str) -> HistoryItem:
        history = self.history_store.read()
        items = history.get("items", [])
        matched = next(
            (entry for entry in items if entry.get("payload", {}).get("id") == item_id),
            None,
        )
        if not matched:
            raise NotFoundError(f"History item not found: {item_id}")
        return HistoryItem.model_validate(matched)

    def _append_history(self, item: dict) -> None:
        history = self.history_store.read()
        history.setdefault("items", []).append(item)
        self.history_store.write(history)
