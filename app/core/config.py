from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Copilot"
    app_env: str = "local"
    log_level: str = "INFO"
    data_dir: str = "data"
    outputs_dir: str = "outputs"
    workspaces_dir: str = "workspaces"
    notebooklm_connector_mode: str = "stub"
    notebooklm_bridge_command: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def data_path(self) -> Path:
        return (self.root_dir / self.data_dir).resolve()

    @property
    def outputs_path(self) -> Path:
        return (self.root_dir / self.outputs_dir).resolve()

    @property
    def workspaces_path(self) -> Path:
        return (self.root_dir / self.workspaces_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
