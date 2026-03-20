from __future__ import annotations

from app.models.artifact import ArtifactItem
from app.models.query import AskResponse
from app.models.report import BatchResearchResponse, ResearchResponse
from app.models.snapshot import SnapshotDiffResponse, SnapshotEntry
from app.storage.file_store import FileStore


class ExportService:
    def __init__(self, file_store: FileStore) -> None:
        self.file_store = file_store

    def export_answer(self, response: AskResponse) -> AskResponse:
        markdown = self._build_answer_markdown(response)
        md_path = self.file_store.save_markdown(response.question, markdown, prefix="answer")
        json_path = self.file_store.save_json(
            response.question, response.model_dump(mode="json"), prefix="answer"
        )
        response.output_markdown_path = str(md_path)
        response.output_json_path = str(json_path)
        return response

    def export_research(self, response: ResearchResponse) -> ResearchResponse:
        markdown = self._build_research_markdown(response)
        md_path = self.file_store.save_markdown(response.topic, markdown, prefix="research")
        json_path = self.file_store.save_json(
            response.topic, response.model_dump(mode="json"), prefix="research"
        )
        response.output_markdown_path = str(md_path)
        response.output_json_path = str(json_path)
        return response

    def export_batch_research(self, response: BatchResearchResponse) -> BatchResearchResponse:
        markdown = self._build_batch_markdown(response)
        md_path = self.file_store.save_markdown(
            f"batch-{response.template_name}", markdown, prefix="batch-research"
        )
        json_path = self.file_store.save_json(
            f"batch-{response.template_name}",
            response.model_dump(mode="json"),
            prefix="batch-research",
        )
        response.output_markdown_path = str(md_path)
        response.output_json_path = str(json_path)
        return response

    def export_artifact_bundle(self, bundle_name: str, items: list[ArtifactItem]) -> dict[str, str]:
        markdown = self._build_bundle_markdown(bundle_name, items)
        payload = {
            "bundle_name": bundle_name,
            "included_count": len(items),
            "items": [item.model_dump(mode="json") for item in items],
        }
        md_path = self.file_store.save_markdown(bundle_name, markdown, prefix="bundle")
        json_path = self.file_store.save_json(bundle_name, payload, prefix="bundle")
        return {"markdown": str(md_path), "json": str(json_path)}

    def export_snapshot(self, snapshot: SnapshotEntry) -> SnapshotEntry:
        markdown = self._build_snapshot_markdown(snapshot)
        md_path = self.file_store.save_markdown(
            f"{snapshot.view_name}-{snapshot.id}", markdown, prefix="snapshot"
        )
        json_path = self.file_store.save_json(
            f"{snapshot.view_name}-{snapshot.id}",
            snapshot.model_dump(mode="json"),
            prefix="snapshot",
        )
        snapshot.output_markdown_path = str(md_path)
        snapshot.output_json_path = str(json_path)
        return snapshot

    def export_snapshot_diff(self, diff: SnapshotDiffResponse) -> dict[str, str]:
        markdown = self._build_snapshot_diff_markdown(diff)
        md_path = self.file_store.save_markdown(
            f"diff-{diff.from_snapshot_id[:8]}-{diff.to_snapshot_id[:8]}",
            markdown,
            prefix="snapshot-diff",
        )
        json_path = self.file_store.save_json(
            f"diff-{diff.from_snapshot_id[:8]}-{diff.to_snapshot_id[:8]}",
            diff.model_dump(mode="json"),
            prefix="snapshot-diff",
        )
        return {"markdown": str(md_path), "json": str(json_path)}

    def _build_answer_markdown(self, response: AskResponse) -> str:
        sources = "\n".join(f"- {source}" for source in response.sources) or "- No sources"
        return (
            f"# Answer\n\n"
            f"## Question\n{response.question}\n\n"
            f"## Notebook\n- id: `{response.notebook_id}`\n- url: {response.notebook_url}\n\n"
            f"## Artifact Type\n{response.artifact_type}\n\n"
            f"## Response\n{response.answer}\n\n"
            f"## Sources\n{sources}\n"
        )

    def _build_research_markdown(self, response: ResearchResponse) -> str:
        lines = [
            "# Research Report",
            "",
            f"## Topic\n{response.topic}",
            "",
            "## Metadata",
            f"- notebook_id: `{response.notebook_id}`",
            f"- artifact_type: `{response.artifact_type}`",
            "",
            "## Findings",
        ]
        for index, item in enumerate(response.items, start=1):
            lines.append(f"### {index}. {item.question}")
            lines.append(item.answer)
            lines.append("")
            lines.append("Sources:")
            if item.sources:
                lines.extend([f"- {source}" for source in item.sources])
            else:
                lines.append("- No sources")
            lines.append("")
        return "\n".join(lines)

    def _build_batch_markdown(self, response: BatchResearchResponse) -> str:
        lines = [
            "# Batch Research Report",
            "",
            "## Metadata",
            f"- template_name: `{response.template_name}`",
            f"- artifact_type: `{response.artifact_type}`",
            f"- notebook_id: `{response.notebook_id}`",
            f"- completed_topics: {len(response.items)}",
            f"- failed_topics: {len(response.failures)}",
            "",
            "## Topic Reports",
        ]
        for item in response.items:
            lines.append(f"- `{item.topic}` -> `{item.output_markdown_path}`")
        if not response.items:
            lines.append("- No successful reports.")
        lines.append("")
        lines.append("## Failures")
        for failure in response.failures:
            lines.append(f"- {failure.topic}: {failure.error}")
        if not response.failures:
            lines.append("- No failures.")
        return "\n".join(lines)

    def _build_bundle_markdown(self, bundle_name: str, items: list[ArtifactItem]) -> str:
        lines = [
            "# Artifact Bundle",
            "",
            "## Metadata",
            f"- bundle_name: `{bundle_name}`",
            f"- included_count: {len(items)}",
            "",
            "## Included Artifacts",
        ]
        for item in items:
            lines.append(f"### {item.type}: {item.title}")
            lines.append(f"- id: `{item.id}`")
            lines.append(f"- template: `{item.template_name}`")
            lines.append(f"- markdown: `{item.markdown_path}`")
            lines.append(f"- json: `{item.json_path}`")
            lines.append("")
        if not items:
            lines.append("- No artifacts included.")
        return "\n".join(lines)

    def _build_snapshot_markdown(self, snapshot: SnapshotEntry) -> str:
        lines = [
            "# Search View Snapshot",
            "",
            "## Metadata",
            f"- snapshot_id: `{snapshot.id}`",
            f"- view_name: `{snapshot.view_name}`",
            f"- scope: `{snapshot.scope}`",
            f"- item_count: {snapshot.item_count}",
            f"- created_at: {snapshot.created_at.isoformat()}",
            "",
            "## Changelog",
            f"- added_ids: {len(snapshot.changelog.added_ids)}",
            f"- removed_ids: {len(snapshot.changelog.removed_ids)}",
            "",
            "## Items",
        ]
        for item in snapshot.items:
            title = item.get("title") or item.get("name") or item.get("id")
            lines.append(f"- `{item.get('id', '')}`: {title}")
        if not snapshot.items:
            lines.append("- No items in snapshot.")
        return "\n".join(lines)

    def _build_snapshot_diff_markdown(self, diff: SnapshotDiffResponse) -> str:
        summary = diff.summary
        net_change = int(summary.get("net_change", diff.to_item_count - diff.from_item_count))
        change_ratio = float(summary.get("change_ratio_from", 0.0))
        retention_from = float(summary.get("retention_ratio_from", 0.0))
        retention_to = float(summary.get("retention_ratio_to", 0.0))
        lines = [
            "# Snapshot Diff Report",
            "",
            "## Executive Summary",
            f"- net_change: {net_change:+d} items ({diff.from_item_count} -> {diff.to_item_count})",
            f"- churn_ratio_from: {change_ratio:.2%}",
            f"- retention_ratio_from: {retention_from:.2%}",
            f"- retention_ratio_to: {retention_to:.2%}",
            "",
            "## Metadata",
            f"- from_snapshot_id: `{diff.from_snapshot_id}`",
            f"- to_snapshot_id: `{diff.to_snapshot_id}`",
            f"- from_view_name: `{diff.from_view_name}`",
            f"- to_view_name: `{diff.to_view_name}`",
            f"- from_item_count: {diff.from_item_count}",
            f"- to_item_count: {diff.to_item_count}",
            "",
            "## Changes Summary",
            f"- added: {len(diff.added_ids)}",
            f"- removed: {len(diff.removed_ids)}",
            f"- common: {len(diff.common_ids)}",
            "",
            "## Added IDs",
        ]
        lines.extend([f"- {item}" for item in diff.added_ids] or ["- None"])
        lines.append("")
        lines.append("## Removed IDs")
        lines.extend([f"- {item}" for item in diff.removed_ids] or ["- None"])
        lines.append("")
        lines.append("## Common IDs")
        lines.extend([f"- {item}" for item in diff.common_ids] or ["- None"])
        return "\n".join(lines)
