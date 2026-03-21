from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_snapshot_extended_endpoints_smoke() -> None:
    client = TestClient(app)
    suffix = uuid4().hex[:8]
    tag = f"api-extended-{suffix}"
    view_name = f"api-extended-view-{suffix}"

    notebook = client.post(
        "/notebooks",
        json={
            "name": f"API Extended {suffix}",
            "url": f"https://notebooklm.google.com/notebook/{suffix}",
            "tags": [tag],
            "description": "extended snapshot endpoint smoke",
        },
    )
    assert notebook.status_code == 200
    notebook_id = notebook.json()["id"]
    assert client.post("/notebooks/select", json={"notebook_id": notebook_id}).status_code == 200

    view = client.post(
        "/search-views",
        json={
            "name": view_name,
            "scope": "history",
            "item_type": "ask",
            "tag": tag,
            "description": "extended endpoint view",
        },
    )
    assert view.status_code == 200

    snapshot_ids: list[str] = []
    for idx in range(1, 4):
        ask = client.post(
            "/ask",
            json={
                "question": f"endpoint smoke question {idx} {suffix}",
                "artifact_type": "summary",
                "tags": [tag],
            },
        )
        assert ask.status_code == 200
        created = client.post("/snapshots", json={"view_name": view_name})
        assert created.status_code == 200
        snapshot_ids.append(created.json()["id"])

    diff_latest = client.get("/snapshots/diff/latest", params={"view_name": view_name})
    assert diff_latest.status_code == 200

    latest_brief = client.get(
        "/snapshots/diff/latest/brief",
        params={"view_name": view_name, "top_items": 3},
    )
    assert latest_brief.status_code == 200
    assert latest_brief.json()["view_name"] == view_name

    pair_brief = client.post(
        "/snapshots/diff/brief",
        params={"top_items": 3},
        json={"from_snapshot_id": snapshot_ids[0], "to_snapshot_id": snapshot_ids[-1]},
    )
    assert pair_brief.status_code == 200

    trend = client.post("/snapshots/trend", json={"view_name": view_name, "limit": 3})
    assert trend.status_code == 200
    assert trend.json()["compared_pairs"] >= 1

    trend_export = client.post("/snapshots/trend/export", json={"view_name": view_name, "limit": 3})
    assert trend_export.status_code == 200
    assert "markdown" in trend_export.json()
    assert "json_path" in trend_export.json()

    update_pack = client.post(
        "/snapshots/update-pack",
        json={"view_name": view_name, "top_items": 3, "trend_limit": 3},
    )
    assert update_pack.status_code == 200
    assert update_pack.json()["view_name"] == view_name

    update_pack_export = client.post(
        "/snapshots/update-pack/export",
        json={"view_name": view_name, "top_items": 3, "trend_limit": 3},
    )
    assert update_pack_export.status_code == 200
    assert "markdown" in update_pack_export.json()
    assert "json_path" in update_pack_export.json()
