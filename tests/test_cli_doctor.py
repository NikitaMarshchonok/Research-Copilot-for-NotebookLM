from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import app.cli as cli_module


def _mock_container(base_dir: Path, bridge_mode: bool = False, bridge_command: str = "") -> SimpleNamespace:
    workspace_data = base_dir / "data"
    workspace_outputs = base_dir / "outputs"
    workspaces_root = base_dir / "workspaces"
    workspace_data.mkdir(parents=True, exist_ok=True)
    workspace_outputs.mkdir(parents=True, exist_ok=True)
    workspaces_root.mkdir(parents=True, exist_ok=True)

    settings = SimpleNamespace(
        root_dir=Path(".").resolve(),
        workspaces_path=workspaces_root,
        notebooklm_connector_mode="bridge" if bridge_mode else "stub",
        notebooklm_bridge_command=bridge_command,
    )
    workspace_service = SimpleNamespace(
        get_current_response=lambda: SimpleNamespace(
            active_workspace="default",
            data_path=workspace_data,
            outputs_path=workspace_outputs,
        )
    )
    return SimpleNamespace(settings=settings, workspace_service=workspace_service)


def _test_dir() -> Path:
    base_dir = Path(".pytest_runtime") / f"doctor-{uuid4().hex[:8]}"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_doctor_checks_ok() -> None:
    container = _mock_container(_test_dir())
    active_workspace, connector_mode, checks = cli_module._doctor_checks(
        container=container,
        npx_path="/usr/bin/npx",
    )
    assert active_workspace == "default"
    assert connector_mode == "stub"
    assert all(condition for _, condition, _ in checks)


def test_doctor_checks_bridge_mode_warnings() -> None:
    container = _mock_container(_test_dir(), bridge_mode=True, bridge_command="")
    _, connector_mode, checks = cli_module._doctor_checks(
        container=container,
        npx_path=None,
    )
    assert connector_mode == "bridge"
    mapped = {name: condition for name, condition, _ in checks}
    assert mapped["npx installed"] is False
    assert mapped["bridge command configured"] is False
