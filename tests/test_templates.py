from pathlib import Path

from app.models.template import TemplateCreateRequest
from app.services.template_service import TemplateService
from app.storage.json_store import JsonStore


def test_template_service_seeds_defaults_and_adds_custom(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "templates.json", {"items": []})
    service = TemplateService(store)
    defaults = service.list_templates()
    assert any(item.name == "study_guide" for item in defaults)

    created = service.add_template(
        TemplateCreateRequest(
            name="my-template",
            description="custom",
            questions=["What is {topic}?", "How to start with {topic}?"],
            artifact_type="summary",
        )
    )
    assert created.name == "my-template"

    questions, artifact_type = service.render_questions("my-template", "MCP")
    assert questions[0] == "What is MCP?"
    assert artifact_type == "summary"
