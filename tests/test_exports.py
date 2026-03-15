from pathlib import Path

from app.models.query import AskResponse
from app.services.export_service import ExportService
from app.storage.file_store import FileStore


def test_export_answer_creates_files(tmp_path: Path) -> None:
    service = ExportService(FileStore(tmp_path))
    response = AskResponse(
        notebook_id="n1",
        notebook_url="https://notebooklm.google.com/notebook/test",
        question="What is MCP?",
        answer="MCP is a protocol for connecting tools.",
        sources=["source-1"],
    )
    exported = service.export_answer(response)

    assert exported.output_markdown_path is not None
    assert exported.output_json_path is not None
    assert Path(exported.output_markdown_path).exists()
    assert Path(exported.output_json_path).exists()
