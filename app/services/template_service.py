from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.template import TemplateCreateRequest, TemplateEntry
from app.services.prompt_templates import DEFAULT_RESEARCH_TEMPLATES
from app.storage.json_store import JsonStore


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TemplateService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.store.ensure()
        self._ensure_default_templates()

    def _ensure_default_templates(self) -> None:
        data = self.store.read()
        items = data.get("items", [])
        existing_names = {item.get("name", "").strip().lower() for item in items}
        changed = False
        for name, meta in DEFAULT_RESEARCH_TEMPLATES.items():
            if name in existing_names:
                continue
            items.append(
                TemplateEntry(
                    name=name,
                    description=str(meta.get("description", "")),
                    questions=[str(q) for q in meta.get("questions", [])],
                    artifact_type=str(meta.get("artifact_type", "study_guide")),
                ).model_dump(mode="json")
            )
            changed = True
        if changed:
            self.store.write({"items": items})

    def list_templates(self) -> list[TemplateEntry]:
        data = self.store.read()
        return [TemplateEntry.model_validate(item) for item in data.get("items", [])]

    def add_template(self, payload: TemplateCreateRequest) -> TemplateEntry:
        data = self.store.read()
        items = data.get("items", [])
        normalized = payload.name.strip().lower()
        if any(str(item.get("name", "")).strip().lower() == normalized for item in items):
            raise ValidationAppError(f"Template '{payload.name}' already exists.")
        template = TemplateEntry(**payload.model_dump())
        items.append(template.model_dump(mode="json"))
        self.store.write({"items": items})
        return template

    def get_template_by_name(self, name: str) -> TemplateEntry:
        normalized = name.strip().lower()
        for template in self.list_templates():
            if template.name.strip().lower() == normalized:
                return template
        raise NotFoundError(f"Template '{name}' not found.")

    def render_questions(self, template_name: str, topic: str) -> tuple[list[str], str]:
        template = self.get_template_by_name(template_name)
        rendered = [question.format(topic=topic) for question in template.questions]
        return rendered, template.artifact_type
