from __future__ import annotations

from app.models.query import AskResponse
from app.models.report import ResearchResponse
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
