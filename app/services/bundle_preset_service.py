from __future__ import annotations

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.bundle_preset import BundlePresetCreateRequest, BundlePresetEntry
from app.storage.json_store import JsonStore

DEFAULT_BUNDLE_PRESETS: dict[str, dict[str, object]] = {
    "article-pack": {
        "description": "Balanced pack for article drafting.",
        "item_types": ["research", "ask", "batch_research"],
    },
    "tech-brief-pack": {
        "description": "Focus on research and batch summaries.",
        "item_types": ["research", "batch_research"],
    },
    "study-pack": {
        "description": "Study-oriented pack with ask + research.",
        "item_types": ["research", "ask"],
    },
}


class BundlePresetService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.store.ensure()
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        data = self.store.read()
        items = data.get("items", [])
        existing = {str(item.get("name", "")).strip().lower() for item in items}
        changed = False
        for name, preset in DEFAULT_BUNDLE_PRESETS.items():
            if name in existing:
                continue
            items.append(
                BundlePresetEntry(
                    name=name,
                    description=str(preset.get("description", "")),
                    item_types=[str(t) for t in preset.get("item_types", [])],  # type: ignore[list-item]
                ).model_dump(mode="json")
            )
            changed = True
        if changed:
            self.store.write({"items": items})

    def list_presets(self) -> list[BundlePresetEntry]:
        data = self.store.read()
        return [BundlePresetEntry.model_validate(item) for item in data.get("items", [])]

    def add_preset(self, payload: BundlePresetCreateRequest) -> BundlePresetEntry:
        data = self.store.read()
        items = data.get("items", [])
        normalized = payload.name.strip().lower()
        if any(str(item.get("name", "")).strip().lower() == normalized for item in items):
            raise ValidationAppError(f"Bundle preset '{payload.name}' already exists.")
        entry = BundlePresetEntry(**payload.model_dump())
        items.append(entry.model_dump(mode="json"))
        self.store.write({"items": items})
        return entry

    def delete_preset(self, name: str) -> None:
        normalized = name.strip().lower()
        data = self.store.read()
        items = data.get("items", [])
        filtered = [item for item in items if str(item.get("name", "")).strip().lower() != normalized]
        if len(filtered) == len(items):
            raise NotFoundError(f"Bundle preset '{name}' not found.")
        if normalized in DEFAULT_BUNDLE_PRESETS:
            raise ValidationAppError("Default bundle presets cannot be deleted.")
        self.store.write({"items": filtered})

    def get_item_types(self, name: str) -> list[str]:
        normalized = name.strip().lower()
        for preset in self.list_presets():
            if preset.name.strip().lower() == normalized:
                return [str(item) for item in preset.item_types]
        raise NotFoundError(f"Bundle preset '{name}' not found.")
