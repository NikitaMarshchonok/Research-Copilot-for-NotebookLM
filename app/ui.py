from __future__ import annotations

import os
import requests
import streamlit as st

API_BASE = os.getenv("RESEARCH_COPILOT_API_BASE", "http://127.0.0.1:8000")
ARTIFACT_TYPES = ["summary", "faq", "comparison", "study_guide", "implementation_notes"]

st.set_page_config(page_title="Research Copilot", layout="wide")
st.title("Research Copilot + NotebookLM")

def api_get(path: str) -> dict | list:
    response = requests.get(f"{API_BASE}{path}", timeout=30)
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
    if st.button("Run Ask"):
        try:
            result = api_post("/ask", {"question": question, "artifact_type": artifact_type})
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
if st.button("Run Research"):
    questions = [line.strip() for line in questions_raw.splitlines() if line.strip()]
    if not questions:
        st.error("Please provide at least one question.")
    else:
        try:
            report = api_post(
                "/research",
                {"topic": topic, "questions": questions, "artifact_type": research_artifact},
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
    if st.button("Run Template Research", disabled=not bool(template_names)):
        try:
            report = api_post(
                "/research/template",
                {
                    "topic": single_topic,
                    "template_name": selected_template,
                    "artifact_type": template_override_artifact,
                },
            )
            st.json(report)
        except requests.RequestException as exc:
            st.error(f"Template research failed: {exc}")

st.subheader("Batch Template Research")
batch_topics_raw = st.text_area("Batch topics (one per line)", height=120)
batch_continue = st.checkbox("Continue on error", value=True)
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
                    "continue_on_error": batch_continue,
                },
            )
            st.json(batch)
        except requests.RequestException as exc:
            st.error(f"Batch template research failed: {exc}")

st.subheader("History")
if st.button("Refresh History"):
    try:
        history = api_get("/history")
        st.json(history)
    except requests.RequestException as exc:
        st.error(f"History load failed: {exc}")

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
if st.button("Refresh Artifacts"):
    try:
        path = "/artifacts"
        if artifact_filter != "all":
            path = f"/artifacts?item_type={artifact_filter}"
        artifacts = api_get(path)
        st.json(artifacts)
    except requests.RequestException as exc:
        st.error(f"Artifacts load failed: {exc}")

artifact_col_1, artifact_col_2 = st.columns(2)
with artifact_col_1:
    if st.button("Get Latest Artifact"):
        try:
            path = "/artifacts/latest"
            params = []
            if artifact_filter != "all":
                params.append(f"item_type={artifact_filter}")
            if latest_template_filter.strip():
                params.append(f"template_name={latest_template_filter.strip()}")
            if params:
                path = f"{path}?{'&'.join(params)}"
            latest = api_get(path)
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
            exported = api_post("/exports/latest", payload)
            st.json(exported)
        except requests.RequestException as exc:
            st.error(f"Latest artifact export failed: {exc}")
