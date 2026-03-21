from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from app.cli import app as cli_app
from app.main import app


def test_snapshot_digest_and_update_pack_api_smoke() -> None:
    suffix = uuid4().hex[:8]
    tag = f"smoke-{suffix}"
    view_name = f"smoke-view-{suffix}"
    client = TestClient(app)

    notebook = client.post(
        "/notebooks",
        json={
            "name": f"Smoke Notebook {suffix}",
            "url": f"https://notebooklm.google.com/notebook/{suffix}",
            "tags": [tag],
            "description": "snapshot smoke test",
        },
    )
    assert notebook.status_code == 200
    notebook_id = notebook.json()["id"]
    select = client.post("/notebooks/select", json={"notebook_id": notebook_id})
    assert select.status_code == 200

    view = client.post(
        "/search-views",
        json={
            "name": view_name,
            "scope": "history",
            "item_type": "ask",
            "tag": tag,
            "description": "API smoke view",
        },
    )
    assert view.status_code == 200

    ask_payload = {"artifact_type": "summary", "tags": [tag]}
    for idx in range(1, 4):
        ask = client.post("/ask", json={"question": f"api smoke question {idx} {suffix}", **ask_payload})
        assert ask.status_code == 200
        snapshot = client.post("/snapshots", json={"view_name": view_name})
        assert snapshot.status_code == 200

    digest = client.post(
        "/snapshots/diff/digest",
        json={"view_names": [view_name], "top_items": 3, "include_missing": True},
    )
    assert digest.status_code == 200
    digest_body = digest.json()
    assert digest_body["included_count"] == 1
    assert digest_body["items"][0]["view_name"] == view_name

    update_pack = client.post(
        "/snapshots/update-pack",
        json={"view_name": view_name, "top_items": 3, "trend_limit": 3},
    )
    assert update_pack.status_code == 200
    pack_body = update_pack.json()
    assert pack_body["view_name"] == view_name
    assert len(pack_body["trend"]["points"]) >= 2

    digest_export = client.post(
        "/snapshots/diff/digest/export",
        json={"view_names": [view_name], "top_items": 3, "include_missing": True},
    )
    assert digest_export.status_code == 200
    digest_paths = digest_export.json()
    assert Path(digest_paths["markdown"]).exists()
    assert Path(digest_paths["json_path"]).exists()

    pack_export = client.post(
        "/snapshots/update-pack/export",
        json={"view_name": view_name, "top_items": 3, "trend_limit": 3},
    )
    assert pack_export.status_code == 200
    pack_paths = pack_export.json()
    assert Path(pack_paths["markdown"]).exists()
    assert Path(pack_paths["json_path"]).exists()


def test_snapshot_digest_and_update_pack_cli_smoke() -> None:
    runner = CliRunner()
    suffix = uuid4().hex[:8]
    tag = f"cli-smoke-{suffix}"
    view_name = f"cli-view-{suffix}"

    add = runner.invoke(
        cli_app,
        [
            "notebooks",
            "add",
            "--name",
            f"CLI Smoke {suffix}",
            "--url",
            f"https://notebooklm.google.com/notebook/{suffix}",
            "--tags",
            tag,
            "--description",
            "cli smoke",
        ],
    )
    assert add.exit_code == 0
    notebook_id = add.stdout.strip().split(":")[-1].strip()
    assert notebook_id

    select = runner.invoke(cli_app, ["notebooks", "select", notebook_id])
    assert select.exit_code == 0

    add_view = runner.invoke(
        cli_app,
        ["views", "add", "--name", view_name, "--scope", "history", "--type", "ask", "--tag", tag],
    )
    assert add_view.exit_code == 0

    for idx in range(1, 4):
        ask = runner.invoke(
            cli_app,
            [
                "ask",
                "--question",
                f"cli smoke question {idx} {suffix}",
                "--artifact-type",
                "summary",
                "--tag",
                tag,
            ],
        )
        assert ask.exit_code == 0
        create_snapshot = runner.invoke(cli_app, ["snapshots", "create", "--view", view_name])
        assert create_snapshot.exit_code == 0

    digest = runner.invoke(cli_app, ["snapshots", "digest", "--view", view_name, "--top", "3"])
    assert digest.exit_code == 0
    assert '"included_count": 1' in digest.stdout

    pack = runner.invoke(
        cli_app,
        ["snapshots", "update-pack", "--view", view_name, "--top", "3", "--trend-limit", "3"],
    )
    assert pack.exit_code == 0
    assert f'"view_name": "{view_name}"' in pack.stdout

    digest_export = runner.invoke(
        cli_app,
        ["snapshots", "digest-export", "--view", view_name, "--top", "3", "--include-missing"],
    )
    assert digest_export.exit_code == 0
    assert '"markdown"' in digest_export.stdout
    assert '"json"' in digest_export.stdout

    pack_export = runner.invoke(
        cli_app,
        ["snapshots", "update-pack-export", "--view", view_name, "--top", "3", "--trend-limit", "3"],
    )
    assert pack_export.exit_code == 0
    assert '"markdown"' in pack_export.stdout
    assert '"json"' in pack_export.stdout
