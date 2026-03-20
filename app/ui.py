from __future__ import annotations

import os
import requests
import streamlit as st

API_BASE = os.getenv("RESEARCH_COPILOT_API_BASE", "http://127.0.0.1:8000")
ARTIFACT_TYPES = ["summary", "faq", "comparison", "study_guide", "implementation_notes"]

st.set_page_config(page_title="Research Copilot", layout="wide")
st.title("Research Copilot + NotebookLM")

def api_get(path: str, params: dict | None = None) -> dict | list:
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict) -> dict:
    response = requests.post(f"{API_BASE}{path}", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


st.subheader("Workspace")
try:
    current_workspace = api_get("/workspaces/current")
    st.caption(
        f"Active: {current_workspace['active_workspace']} | "
        f"data: {current_workspace['data_path']} | outputs: {current_workspace['outputs_path']}"
    )
    workspaces = api_get("/workspaces")
    workspace_names = [item["name"] for item in workspaces]
    workspace_col_1, workspace_col_2 = st.columns(2)
    with workspace_col_1:
        selected_workspace = st.selectbox("Select workspace", workspace_names, key="workspace_select")
        if st.button("Switch Workspace"):
            api_post("/workspaces/select", {"name": selected_workspace})
            st.success(f"Workspace switched to: {selected_workspace}")
    with workspace_col_2:
        with st.form("create_workspace"):
            workspace_name = st.text_input("New workspace name")
            workspace_description = st.text_input("Workspace description")
            create_workspace = st.form_submit_button("Create Workspace")
            if create_workspace:
                created = api_post(
                    "/workspaces",
                    {"name": workspace_name, "description": workspace_description},
                )
                st.success(f"Workspace created: {created['name']}")
except requests.RequestException as exc:
    st.warning(f"Could not load workspaces: {exc}")


left, right = st.columns(2)

with left:
    st.subheader("Notebook Registry")
    with st.form("add_notebook"):
        name = st.text_input("Name")
        url = st.text_input("Notebook URL")
        tags = st.text_input("Tags (comma separated)")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Add Notebook")
        if submitted:
            try:
                added = api_post(
                    "/notebooks",
                    {
                        "name": name,
                        "url": url,
                        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                        "description": description,
                    },
                )
                st.success(f"Notebook added: {added['id']}")
            except requests.RequestException as exc:
                st.error(f"Request failed: {exc}")

    try:
        notebooks = api_get("/notebooks")
        active = api_get("/notebooks/active")
        notebook_map = {entry["name"]: entry["id"] for entry in notebooks}
        selected_name = st.selectbox(
            "Select active notebook",
            options=list(notebook_map.keys()) or ["<no notebooks>"],
        )
        if st.button("Set Active Notebook"):
            if notebooks:
                selected_id = notebook_map[selected_name]
                api_post("/notebooks/select", {"notebook_id": selected_id})
                st.success(f"Active notebook set: {selected_name}")
        st.caption(f"Current active: {active.get('active_notebook_id')}")
    except requests.RequestException as exc:
        st.warning(f"Could not load notebooks: {exc}")

with right:
    st.subheader("Ask NotebookLM")
    question = st.text_area("Question", height=120)
    artifact_type = st.selectbox(
        "Artifact type",
        ["summary", "faq", "comparison", "study_guide", "implementation_notes"],
    )
    ask_tags_raw = st.text_input("Ask tags (comma separated)")
    if st.button("Run Ask"):
        try:
            result = api_post(
                "/ask",
                {
                    "question": question,
                    "artifact_type": artifact_type,
                    "tags": [tag.strip() for tag in ask_tags_raw.split(",") if tag.strip()],
                },
            )
            st.json(result)
        except requests.RequestException as exc:
            st.error(f"Ask failed: {exc}")

st.subheader("Research Mode")
topic = st.text_input("Topic")
questions_raw = st.text_area("Questions (one per line)", height=120)
research_artifact = st.selectbox(
    "Research artifact type",
    ["study_guide", "summary", "faq", "comparison", "implementation_notes"],
)
research_tags_raw = st.text_input("Research tags (comma separated)")
if st.button("Run Research"):
    questions = [line.strip() for line in questions_raw.splitlines() if line.strip()]
    if not questions:
        st.error("Please provide at least one question.")
    else:
        try:
            report = api_post(
                "/research",
                {
                    "topic": topic,
                    "questions": questions,
                    "artifact_type": research_artifact,
                    "tags": [tag.strip() for tag in research_tags_raw.split(",") if tag.strip()],
                },
            )
            st.json(report)
        except requests.RequestException as exc:
            st.error(f"Research failed: {exc}")

st.subheader("Template-driven Research")
templates: list[dict] = []
template_map: dict[str, dict] = {}

try:
    templates = api_get("/templates")
    template_map = {entry["name"]: entry for entry in templates}
except requests.RequestException as exc:
    st.warning(f"Could not load templates: {exc}")

template_left, template_right = st.columns(2)

with template_left:
    with st.form("add_template"):
        st.caption("Create custom template")
        template_name = st.text_input("Template name")
        template_description = st.text_area("Template description", height=80)
        template_questions_raw = st.text_area(
            "Template questions (one per line, use {topic} placeholder)",
            height=120,
        )
        template_artifact = st.selectbox("Template artifact type", ARTIFACT_TYPES, key="template_artifact")
        template_submitted = st.form_submit_button("Add Template")
        if template_submitted:
            questions = [line.strip() for line in template_questions_raw.splitlines() if line.strip()]
            if not questions:
                st.error("Template must contain at least one question.")
            else:
                try:
                    created = api_post(
                        "/templates",
                        {
                            "name": template_name,
                            "description": template_description,
                            "questions": questions,
                            "artifact_type": template_artifact,
                        },
                    )
                    st.success(f"Template added: {created['name']}")
                except requests.RequestException as exc:
                    st.error(f"Template creation failed: {exc}")

with template_right:
    template_names = sorted(template_map.keys())
    selected_template = st.selectbox(
        "Template",
        options=template_names or ["<no templates>"],
        key="selected_template",
    )
    if template_names:
        st.caption(template_map[selected_template].get("description", ""))
        st.write("Questions:")
        for index, question_text in enumerate(template_map[selected_template].get("questions", []), start=1):
            st.write(f"{index}. {question_text}")

    single_topic = st.text_input("Template run topic")
    template_override_artifact = st.selectbox(
        "Override artifact type (optional behavior: same value still valid)",
        ARTIFACT_TYPES,
        key="template_override_artifact",
    )
    template_run_tags_raw = st.text_input("Template run tags (comma separated)")
    if st.button("Run Template Research", disabled=not bool(template_names)):
        try:
            report = api_post(
                "/research/template",
                {
                    "topic": single_topic,
                    "template_name": selected_template,
                    "artifact_type": template_override_artifact,
                    "tags": [tag.strip() for tag in template_run_tags_raw.split(",") if tag.strip()],
                },
            )
            st.json(report)
        except requests.RequestException as exc:
            st.error(f"Template research failed: {exc}")

st.subheader("Batch Template Research")
batch_topics_raw = st.text_area("Batch topics (one per line)", height=120)
batch_continue = st.checkbox("Continue on error", value=True)
batch_tags_raw = st.text_input("Batch tags (comma separated)")
if st.button("Run Batch Template Research", disabled=not bool(template_map)):
    topics = [line.strip() for line in batch_topics_raw.splitlines() if line.strip()]
    if not topics:
        st.error("Please provide at least one topic for batch run.")
    else:
        try:
            batch = api_post(
                "/research/batch-template",
                {
                    "topics": topics,
                    "template_name": selected_template,
                    "tags": [tag.strip() for tag in batch_tags_raw.split(",") if tag.strip()],
                    "continue_on_error": batch_continue,
                },
            )
            st.json(batch)
        except requests.RequestException as exc:
            st.error(f"Batch template research failed: {exc}")

st.subheader("History")
history_filter_col_1, history_filter_col_2, history_filter_col_3 = st.columns(3)
with history_filter_col_1:
    history_type_filter = st.selectbox(
        "History type",
        ["all", "ask", "research", "batch_research"],
        key="history_type_filter",
    )
with history_filter_col_2:
    history_tag_filter = st.text_input("History tag filter", key="history_tag_filter")
with history_filter_col_3:
    history_query_filter = st.text_input("History query filter", key="history_query_filter")
if st.button("Refresh History"):
    try:
        params: dict[str, str] = {}
        if history_type_filter != "all":
            params["item_type"] = history_type_filter
        if history_tag_filter.strip():
            params["tag"] = history_tag_filter.strip()
        if history_query_filter.strip():
            params["query"] = history_query_filter.strip()
        history = api_get("/history", params=params or None)
        st.json(history)
    except requests.RequestException as exc:
        st.error(f"History load failed: {exc}")

st.subheader("Saved Search Views")
search_view_map: dict[str, dict] = {}
try:
    search_views = api_get("/search-views")
    search_view_map = {item["name"]: item for item in search_views}
except requests.RequestException as exc:
    st.warning(f"Could not load search views: {exc}")

with st.form("add_search_view"):
    st.caption("Create a reusable search filter")
    search_view_name = st.text_input("View name")
    search_view_scope = st.selectbox("Scope", ["history", "artifacts"])
    search_view_type = st.selectbox(
        "Type filter",
        ["", "ask", "research", "batch_research"],
        format_func=lambda value: value or "<none>",
    )
    search_view_template = st.text_input("Template filter (artifacts only)")
    search_view_tag = st.text_input("Tag filter")
    search_view_query = st.text_input("Query filter")
    search_view_description = st.text_input("Description")
    add_search_view = st.form_submit_button("Add Search View")
    if add_search_view:
        try:
            created = api_post(
                "/search-views",
                {
                    "name": search_view_name,
                    "scope": search_view_scope,
                    "item_type": search_view_type or None,
                    "template_name": search_view_template or None,
                    "tag": search_view_tag or None,
                    "query": search_view_query or None,
                    "description": search_view_description,
                },
            )
            st.success(f"Search view added: {created['name']}")
        except requests.RequestException as exc:
            st.error(f"Search view creation failed: {exc}")

if search_view_map:
    selected_view = st.selectbox("Saved view", sorted(search_view_map.keys()), key="saved_search_view")
    selected_meta = search_view_map[selected_view]
    st.caption(
        f"scope={selected_meta.get('scope')} | type={selected_meta.get('item_type')} | "
        f"tag={selected_meta.get('tag')} | query={selected_meta.get('query')}"
    )
    view_col_1, view_col_2 = st.columns(2)
    with view_col_1:
        if st.button("Run Saved View"):
            try:
                result = api_get(f"/search-views/{selected_view}/run")
                st.json(result)
            except requests.RequestException as exc:
                st.error(f"Saved view run failed: {exc}")
    with view_col_2:
        if st.button("Delete Saved View"):
            try:
                requests.delete(f"{API_BASE}/search-views/{selected_view}", timeout=30).raise_for_status()
                st.success(f"Search view deleted: {selected_view}")
            except requests.RequestException as exc:
                st.error(f"Saved view delete failed: {exc}")

st.subheader("Materialized Snapshots")
if search_view_map:
    snapshot_view_name = st.selectbox(
        "Snapshot from view",
        sorted(search_view_map.keys()),
        key="snapshot_view_name",
    )
    snapshot_col_1, snapshot_col_2 = st.columns(2)
    with snapshot_col_1:
        if st.button("Create Snapshot"):
            try:
                snapshot = api_post("/snapshots", {"view_name": snapshot_view_name})
                st.json(snapshot)
            except requests.RequestException as exc:
                st.error(f"Snapshot creation failed: {exc}")
    with snapshot_col_2:
        if st.button("Refresh Snapshots"):
            try:
                snapshots = api_get("/snapshots", params={"view_name": snapshot_view_name})
                st.json(snapshots)
            except requests.RequestException as exc:
                st.error(f"Snapshot list failed: {exc}")
    latest_snapshot_diff_col_1, latest_snapshot_diff_col_2 = st.columns(2)
    with latest_snapshot_diff_col_1:
        if st.button("Diff Latest 2 Snapshots (View)"):
            try:
                latest_diff = api_get("/snapshots/diff/latest", params={"view_name": snapshot_view_name})
                st.json(latest_diff)
            except requests.RequestException as exc:
                st.error(f"Latest snapshot diff failed: {exc}")
        if st.button("Brief Latest 2 Snapshots (View)"):
            try:
                latest_brief = api_get(
                    "/snapshots/diff/latest/brief",
                    params={"view_name": snapshot_view_name, "top_items": 5},
                )
                st.text(latest_brief.get("brief", ""))
                st.json(latest_brief)
            except requests.RequestException as exc:
                st.error(f"Latest snapshot brief failed: {exc}")
    with latest_snapshot_diff_col_2:
        if st.button("Export Latest Snapshot Diff (View)"):
            try:
                response = requests.post(
                    f"{API_BASE}/snapshots/diff/latest/export",
                    params={"view_name": snapshot_view_name},
                    timeout=60,
                )
                response.raise_for_status()
                st.json(response.json())
            except requests.RequestException as exc:
                st.error(f"Latest snapshot diff export failed: {exc}")

snapshot_id = st.text_input("Snapshot id (for details)", key="snapshot_id")
if st.button("Get Snapshot by ID"):
    if not snapshot_id.strip():
        st.error("Please provide snapshot id.")
    else:
        try:
            snapshot = api_get(f"/snapshots/{snapshot_id.strip()}")
            st.json(snapshot)
        except requests.RequestException as exc:
            st.error(f"Snapshot fetch failed: {exc}")

st.subheader("Snapshot Diff")
diff_col_1, diff_col_2 = st.columns(2)
with diff_col_1:
    from_snapshot_id = st.text_input("From snapshot id", key="from_snapshot_id")
with diff_col_2:
    to_snapshot_id = st.text_input("To snapshot id", key="to_snapshot_id")

diff_action_col_1, diff_action_col_2 = st.columns(2)
with diff_action_col_1:
    if st.button("Run Snapshot Diff"):
        if not from_snapshot_id.strip() or not to_snapshot_id.strip():
            st.error("Provide both from/to snapshot ids.")
        else:
            try:
                diff = api_post(
                    "/snapshots/diff",
                    {
                        "from_snapshot_id": from_snapshot_id.strip(),
                        "to_snapshot_id": to_snapshot_id.strip(),
                    },
                )
                st.json(diff)
            except requests.RequestException as exc:
                st.error(f"Snapshot diff failed: {exc}")
    if st.button("Generate Diff Brief"):
        if not from_snapshot_id.strip() or not to_snapshot_id.strip():
            st.error("Provide both from/to snapshot ids.")
        else:
            try:
                response = requests.post(
                    f"{API_BASE}/snapshots/diff/brief",
                    params={"top_items": 5},
                    json={
                        "from_snapshot_id": from_snapshot_id.strip(),
                        "to_snapshot_id": to_snapshot_id.strip(),
                    },
                    timeout=60,
                )
                response.raise_for_status()
                brief = response.json()
                st.text(brief.get("brief", ""))
                st.json(brief)
            except requests.RequestException as exc:
                st.error(f"Snapshot diff brief failed: {exc}")

with diff_action_col_2:
    if st.button("Export Snapshot Diff"):
        if not from_snapshot_id.strip() or not to_snapshot_id.strip():
            st.error("Provide both from/to snapshot ids.")
        else:
            try:
                exported = api_post(
                    "/snapshots/diff/export",
                    {
                        "from_snapshot_id": from_snapshot_id.strip(),
                        "to_snapshot_id": to_snapshot_id.strip(),
                    },
                )
                st.json(exported)
            except requests.RequestException as exc:
                st.error(f"Snapshot diff export failed: {exc}")

st.subheader("Snapshot Diff Digest")
digest_views = st.multiselect(
    "Views for digest (empty = all saved views)",
    options=sorted(search_view_map.keys()),
    key="snapshot_digest_views",
)
digest_top = st.slider("Top changed IDs per view", min_value=1, max_value=20, value=5, step=1)
digest_include_missing = st.checkbox(
    "Include skipped/missing views in digest",
    value=True,
    key="snapshot_digest_include_missing",
)
digest_col_1, digest_col_2 = st.columns(2)
with digest_col_1:
    if st.button("Generate Snapshot Digest"):
        try:
            digest = api_post(
                "/snapshots/diff/digest",
                {
                    "view_names": digest_views,
                    "top_items": digest_top,
                    "include_missing": digest_include_missing,
                },
            )
            st.json(digest)
        except requests.RequestException as exc:
            st.error(f"Snapshot digest failed: {exc}")
with digest_col_2:
    if st.button("Export Snapshot Digest"):
        try:
            digest_export = api_post(
                "/snapshots/diff/digest/export",
                {
                    "view_names": digest_views,
                    "top_items": digest_top,
                    "include_missing": digest_include_missing,
                },
            )
            st.json(digest_export)
        except requests.RequestException as exc:
            st.error(f"Snapshot digest export failed: {exc}")

st.subheader("Artifacts Index")
artifact_filter = st.selectbox(
    "Artifact type filter",
    ["all", "ask", "research", "batch_research"],
    key="artifact_filter",
)
latest_template_filter = st.text_input(
    "Latest artifact template filter (optional, for template/batch)",
    key="latest_template_filter",
)
artifact_tag_filter = st.text_input("Artifact tag filter", key="artifact_tag_filter")
artifact_query_filter = st.text_input("Artifact query filter", key="artifact_query_filter")
if st.button("Refresh Artifacts"):
    try:
        params: dict[str, str] = {}
        if artifact_filter != "all":
            params["item_type"] = artifact_filter
        if latest_template_filter.strip():
            params["template_name"] = latest_template_filter.strip()
        if artifact_tag_filter.strip():
            params["tag"] = artifact_tag_filter.strip()
        if artifact_query_filter.strip():
            params["query"] = artifact_query_filter.strip()
        artifacts = api_get("/artifacts", params=params or None)
        st.json(artifacts)
    except requests.RequestException as exc:
        st.error(f"Artifacts load failed: {exc}")

artifact_col_1, artifact_col_2 = st.columns(2)
with artifact_col_1:
    if st.button("Get Latest Artifact"):
        try:
            params: dict[str, str] = {}
            if artifact_filter != "all":
                params["item_type"] = artifact_filter
            if latest_template_filter.strip():
                params["template_name"] = latest_template_filter.strip()
            if artifact_tag_filter.strip():
                params["tag"] = artifact_tag_filter.strip()
            if artifact_query_filter.strip():
                params["query"] = artifact_query_filter.strip()
            latest = api_get("/artifacts/latest", params=params or None)
            st.json(latest)
        except requests.RequestException as exc:
            st.error(f"Latest artifact load failed: {exc}")

with artifact_col_2:
    if st.button("Export Latest Artifact"):
        try:
            payload: dict[str, str] = {}
            if artifact_filter != "all":
                payload["item_type"] = artifact_filter
            if latest_template_filter.strip():
                payload["template_name"] = latest_template_filter.strip()
            if artifact_tag_filter.strip():
                payload["tag"] = artifact_tag_filter.strip()
            if artifact_query_filter.strip():
                payload["query"] = artifact_query_filter.strip()
            exported = api_post("/exports/latest", payload)
            st.json(exported)
        except requests.RequestException as exc:
            st.error(f"Latest artifact export failed: {exc}")

st.subheader("Artifact Bundles")
bundle_preset_map: dict[str, dict] = {}
try:
    bundle_presets = api_get("/bundle-presets")
    bundle_preset_map = {item["name"]: item for item in bundle_presets}
except requests.RequestException as exc:
    st.warning(f"Could not load bundle presets: {exc}")

bundle_names = sorted(bundle_preset_map.keys()) or ["article-pack", "tech-brief-pack", "study-pack"]
bundle_name = st.selectbox("Bundle preset", bundle_names, key="bundle_name")
if bundle_name in bundle_preset_map:
    st.caption(
        f"Types: {', '.join(bundle_preset_map[bundle_name].get('item_types', []))} | "
        f"{bundle_preset_map[bundle_name].get('description', '')}"
    )

with st.form("add_bundle_preset"):
    st.caption("Create custom bundle preset")
    new_bundle_name = st.text_input("Preset name")
    new_bundle_description = st.text_input("Preset description")
    new_bundle_types = st.multiselect(
        "Artifact types in preset",
        ["ask", "research", "batch_research"],
        default=["research", "ask"],
    )
    add_bundle_preset = st.form_submit_button("Add Bundle Preset")
    if add_bundle_preset:
        try:
            created = api_post(
                "/bundle-presets",
                {
                    "name": new_bundle_name,
                    "description": new_bundle_description,
                    "item_types": new_bundle_types,
                },
            )
            st.success(f"Bundle preset added: {created['name']}")
        except requests.RequestException as exc:
            st.error(f"Bundle preset creation failed: {exc}")

if st.button("Delete Selected Bundle Preset"):
    try:
        requests.delete(f"{API_BASE}/bundle-presets/{bundle_name}", timeout=30).raise_for_status()
        st.success(f"Bundle preset deleted: {bundle_name}")
    except requests.RequestException as exc:
        st.error(f"Bundle preset delete failed: {exc}")

bundle_template = st.text_input("Bundle template filter (optional)", key="bundle_template")
if st.button("Export Bundle"):
    try:
        payload: dict[str, str] = {"bundle_name": bundle_name}
        if bundle_template.strip():
            payload["template_name"] = bundle_template.strip()
        bundle = api_post("/exports/bundle", payload)
        st.json(bundle)
    except requests.RequestException as exc:
        st.error(f"Bundle export failed: {exc}")
