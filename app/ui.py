from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

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

st.subheader("History")
if st.button("Refresh History"):
    try:
        history = api_get("/history")
        st.json(history)
    except requests.RequestException as exc:
        st.error(f"History load failed: {exc}")
