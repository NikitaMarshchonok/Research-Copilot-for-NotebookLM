from __future__ import annotations

import logging
from typing import List

from app.core.exceptions import NotFoundError
from app.models.artifact import ArtifactItem
from app.models.bundle_preset import BundlePresetCreateRequest, BundlePresetEntry
from app.models.history import HistoryItem, HistorySummary
from app.models.query import AskRequest, AskResponse
from app.models.report import (
    BatchResearchFailure,
    BatchResearchResponse,
    ResearchRequest,
    ResearchResponse,
)
from app.services.export_service import ExportService
from app.services.bundle_preset_service import BundlePresetService
from app.services.notebook_registry import NotebookRegistryService
from app.services.notebooklm_client import NotebookLMClient
from app.services.prompt_templates import build_question
from app.services.search_view_service import SearchViewService
from app.services.template_service import TemplateService
from app.models.search_view import SearchViewCreateRequest, SearchViewEntry, SearchViewRunResponse
from app.models.snapshot import SnapshotCreateRequest, SnapshotDelta, SnapshotEntry, SnapshotListItem
from app.models.snapshot import SnapshotDiffBriefResponse, SnapshotDiffResponse
from app.storage.json_store import JsonStore

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(
        self,
        registry: NotebookRegistryService,
        template_service: TemplateService,
        bundle_preset_service: BundlePresetService,
        search_view_service: SearchViewService,
        notebooklm_client: NotebookLMClient,
        export_service: ExportService,
        history_store: JsonStore,
        snapshots_store: JsonStore,
    ) -> None:
        self.registry = registry
        self.template_service = template_service
        self.bundle_preset_service = bundle_preset_service
        self.search_view_service = search_view_service
        self.notebooklm_client = notebooklm_client
        self.export_service = export_service
        self.history_store = history_store
        self.snapshots_store = snapshots_store
        self.history_store.ensure()
        self.snapshots_store.ensure()

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
            tags=request.tags,
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
                    tags=request.tags,
                ),
                save_outputs=False,
            )
            items.append(ask_result)

        notebook = self.registry.select_active(request.notebook_id) if request.notebook_id else self.registry.get_active()
        response = ResearchResponse(
            topic=request.topic,
            notebook_id=notebook.id,
            artifact_type=request.artifact_type,
            tags=request.tags,
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
        tags: list[str] | None = None,
    ) -> ResearchResponse:
        questions, template_artifact = self.template_service.render_questions(template_name, topic)
        return self.research(
            ResearchRequest(
                topic=topic,
                questions=questions,
                notebook_id=notebook_id,
                artifact_type=artifact_type or template_artifact,
                tags=tags or [],
            )
        )

    def batch_research_from_template(
        self,
        topics: list[str],
        template_name: str,
        notebook_id: str | None = None,
        artifact_type: str | None = None,
        tags: list[str] | None = None,
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
                    tags=tags,
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
            tags=tags or [],
            items=items,
            failures=failures,
        )
        response = self.export_service.export_batch_research(response)
        self._append_history({"type": "batch_research", "payload": response.model_dump(mode="json")})
        return response

    def list_history(
        self,
        item_type: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[HistorySummary]:
        history = self.history_store.read()
        summaries: list[HistorySummary] = []
        for entry in history.get("items", []):
            payload = entry.get("payload", {})
            entry_type = str(entry.get("type", "ask"))
            tags = [str(value) for value in payload.get("tags", [])]
            title = (
                payload.get("question")
                or payload.get("topic")
                or payload.get("template_name")
                or "Untitled history item"
            )
            if item_type and entry_type != item_type:
                continue
            if tag and tag.strip().lower() not in {value.lower() for value in tags}:
                continue
            if query and query.strip().lower() not in str(title).lower():
                continue
            summaries.append(
                HistorySummary(
                    id=str(payload.get("id", "")),
                    type=entry_type,  # type: ignore[arg-type]
                    created_at=payload.get("created_at"),
                    title=title,
                    tags=tags,
                )
            )
        return summaries

    def list_artifacts(
        self,
        item_type: str | None = None,
        template_name: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[ArtifactItem]:
        history = self.history_store.read()
        artifacts: list[ArtifactItem] = []
        for entry in history.get("items", []):
            entry_type = str(entry.get("type", "ask"))
            if item_type and entry_type != item_type:
                continue
            payload = entry.get("payload", {})
            payload_template = payload.get("template_name")
            payload_tags = [str(value) for value in payload.get("tags", [])]
            if template_name and str(payload_template or "").strip().lower() != template_name.strip().lower():
                continue
            title = (
                payload.get("question")
                or payload.get("topic")
                or payload.get("template_name")
                or "Untitled artifact"
            )
            if tag and tag.strip().lower() not in {value.lower() for value in payload_tags}:
                continue
            if query and query.strip().lower() not in str(title).lower():
                continue
            artifacts.append(
                ArtifactItem(
                    id=str(payload.get("id", "")),
                    type=entry_type,  # type: ignore[arg-type]
                    title=str(title),
                    template_name=str(payload_template) if payload_template else None,
                    tags=payload_tags,
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
        self,
        item_type: str | None = None,
        template_name: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> ArtifactItem:
        artifacts = self.list_artifacts(
            item_type=item_type,
            template_name=template_name,
            tag=tag,
            query=query,
        )
        if not artifacts:
            raise NotFoundError("No artifacts found for the provided filter.")
        return artifacts[0]

    def export_latest_artifact(
        self,
        item_type: str | None = None,
        template_name: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> dict[str, str]:
        latest = self.get_latest_artifact(
            item_type=item_type,
            template_name=template_name,
            tag=tag,
            query=query,
        )
        return self.export_from_history(latest.id)

    def export_artifact_bundle(
        self, bundle_name: str = "article-pack", template_name: str | None = None
    ) -> dict[str, str | int]:
        filters = self.bundle_preset_service.get_item_types(bundle_name)
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

    def list_bundle_presets(self) -> list[BundlePresetEntry]:
        return self.bundle_preset_service.list_presets()

    def add_bundle_preset(self, payload: BundlePresetCreateRequest) -> BundlePresetEntry:
        return self.bundle_preset_service.add_preset(payload)

    def delete_bundle_preset(self, name: str) -> None:
        self.bundle_preset_service.delete_preset(name)

    def list_search_views(self) -> list[SearchViewEntry]:
        return self.search_view_service.list_views()

    def add_search_view(self, payload: SearchViewCreateRequest) -> SearchViewEntry:
        return self.search_view_service.add_view(payload)

    def delete_search_view(self, name: str) -> None:
        self.search_view_service.delete_view(name)

    def run_search_view(self, name: str) -> SearchViewRunResponse:
        view = self.search_view_service.get_view(name)
        if view.scope == "history":
            items = self.list_history(item_type=view.item_type, tag=view.tag, query=view.query)
            serialized = [item.model_dump(mode="json") for item in items]
            return SearchViewRunResponse(
                name=view.name,
                scope=view.scope,
                item_count=len(serialized),
                items=serialized,
            )

        items = self.list_artifacts(
            item_type=view.item_type,
            template_name=view.template_name,
            tag=view.tag,
            query=view.query,
        )
        serialized = [item.model_dump(mode="json") for item in items]
        return SearchViewRunResponse(
            name=view.name,
            scope=view.scope,
            item_count=len(serialized),
            items=serialized,
        )

    def create_snapshot(self, payload: SnapshotCreateRequest) -> SnapshotEntry:
        current = self.run_search_view(payload.view_name)
        previous = self._get_latest_snapshot_for_view(payload.view_name)
        previous_ids = {str(item.get("id", "")) for item in previous.items} if previous else set()
        current_ids = {str(item.get("id", "")) for item in current.items}
        delta = SnapshotDelta(
            added_ids=sorted(current_ids - previous_ids),
            removed_ids=sorted(previous_ids - current_ids),
        )
        snapshot = SnapshotEntry(
            view_name=current.name,
            scope=current.scope,
            item_count=current.item_count,
            changelog=delta,
            items=current.items,
        )
        snapshot = self.export_service.export_snapshot(snapshot)
        data = self.snapshots_store.read()
        data.setdefault("items", []).append(snapshot.model_dump(mode="json"))
        self.snapshots_store.write(data)
        return snapshot

    def list_snapshots(self, view_name: str | None = None) -> list[SnapshotListItem]:
        data = self.snapshots_store.read()
        results: list[SnapshotListItem] = []
        for item in data.get("items", []):
            snapshot = SnapshotEntry.model_validate(item)
            if view_name and snapshot.view_name.strip().lower() != view_name.strip().lower():
                continue
            results.append(
                SnapshotListItem(
                    id=snapshot.id,
                    view_name=snapshot.view_name,
                    scope=snapshot.scope,
                    item_count=snapshot.item_count,
                    created_at=snapshot.created_at,
                    output_markdown_path=snapshot.output_markdown_path,
                    output_json_path=snapshot.output_json_path,
                )
            )
        results.sort(key=lambda item: item.created_at.isoformat(), reverse=True)
        return results

    def get_snapshot(self, snapshot_id: str) -> SnapshotEntry:
        data = self.snapshots_store.read()
        for item in data.get("items", []):
            snapshot = SnapshotEntry.model_validate(item)
            if snapshot.id == snapshot_id:
                return snapshot
        raise NotFoundError(f"Snapshot '{snapshot_id}' not found.")

    def diff_snapshots(self, from_snapshot_id: str, to_snapshot_id: str) -> SnapshotDiffResponse:
        source = self.get_snapshot(from_snapshot_id)
        target = self.get_snapshot(to_snapshot_id)

        source_ids = {str(item.get("id", "")) for item in source.items}
        target_ids = {str(item.get("id", "")) for item in target.items}
        added_ids = sorted(target_ids - source_ids)
        removed_ids = sorted(source_ids - target_ids)
        common_ids = sorted(source_ids & target_ids)
        net_change = target.item_count - source.item_count
        churn = len(added_ids) + len(removed_ids)
        source_count = max(source.item_count, 1)
        target_count = max(target.item_count, 1)
        summary = {
            "from_count": source.item_count,
            "to_count": target.item_count,
            "net_change": net_change,
            "added_count": len(added_ids),
            "removed_count": len(removed_ids),
            "common_count": len(common_ids),
            "change_ratio_from": round(churn / source_count, 4),
            "retention_ratio_from": round(len(common_ids) / source_count, 4),
            "retention_ratio_to": round(len(common_ids) / target_count, 4),
        }

        return SnapshotDiffResponse(
            from_snapshot_id=source.id,
            to_snapshot_id=target.id,
            from_view_name=source.view_name,
            to_view_name=target.view_name,
            from_item_count=source.item_count,
            to_item_count=target.item_count,
            added_ids=added_ids,
            removed_ids=removed_ids,
            common_ids=common_ids,
            summary=summary,
        )

    def export_snapshot_diff(self, from_snapshot_id: str, to_snapshot_id: str) -> dict[str, str]:
        diff = self.diff_snapshots(from_snapshot_id, to_snapshot_id)
        return self.export_service.export_snapshot_diff(diff)

    def diff_latest_snapshots(self, view_name: str) -> SnapshotDiffResponse:
        snapshots = self.list_snapshots(view_name=view_name)
        if len(snapshots) < 2:
            raise NotFoundError(
                f"At least 2 snapshots are required for view '{view_name}' to build latest diff."
            )
        newest = snapshots[0]
        previous = snapshots[1]
        return self.diff_snapshots(previous.id, newest.id)

    def export_latest_snapshot_diff(self, view_name: str) -> dict[str, str]:
        diff = self.diff_latest_snapshots(view_name=view_name)
        return self.export_service.export_snapshot_diff(diff)

    def snapshot_diff_brief(
        self, from_snapshot_id: str, to_snapshot_id: str, top_items: int = 5
    ) -> SnapshotDiffBriefResponse:
        diff = self.diff_snapshots(from_snapshot_id, to_snapshot_id)
        top_limit = max(top_items, 1)
        net_change = int(diff.summary.get("net_change", 0))
        churn_ratio = float(diff.summary.get("change_ratio_from", 0.0))
        retention = float(diff.summary.get("retention_ratio_to", 0.0))
        direction = "grew" if net_change > 0 else "shrunk" if net_change < 0 else "stayed flat"
        brief = (
            f"View '{diff.to_view_name}' {direction}: {diff.from_item_count} -> {diff.to_item_count} "
            f"(net {net_change:+d}), churn {churn_ratio:.1%}, retention {retention:.1%}; "
            f"added {len(diff.added_ids)}, removed {len(diff.removed_ids)}."
        )
        return SnapshotDiffBriefResponse(
            from_snapshot_id=diff.from_snapshot_id,
            to_snapshot_id=diff.to_snapshot_id,
            view_name=diff.to_view_name,
            brief=brief,
            added_count=len(diff.added_ids),
            removed_count=len(diff.removed_ids),
            common_count=len(diff.common_ids),
            top_added_ids=diff.added_ids[:top_limit],
            top_removed_ids=diff.removed_ids[:top_limit],
        )

    def latest_snapshot_diff_brief(self, view_name: str, top_items: int = 5) -> SnapshotDiffBriefResponse:
        latest_diff = self.diff_latest_snapshots(view_name=view_name)
        return self.snapshot_diff_brief(
            from_snapshot_id=latest_diff.from_snapshot_id,
            to_snapshot_id=latest_diff.to_snapshot_id,
            top_items=top_items,
        )

    def _get_latest_snapshot_for_view(self, view_name: str) -> SnapshotEntry | None:
        snapshots = self.list_snapshots(view_name=view_name)
        if not snapshots:
            return None
        return self.get_snapshot(snapshots[0].id)

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
