from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Research Copilot", layout="wide")
st.title("Research Copilot + NotebookLM")

st.subheader("Add notebook")
with st.form("add_notebook"):
    name = st.text_input("Name")
    url = st.text_input("Notebook URL")
    tags = st.text_input("Tags (comma separated)")
    description = st.text_area("Description")
    submitted = st.form_submit_button("Add")
    if submitted:
        response = requests.post(
            f"{API_BASE}/notebooks",
            json={
                "name": name,
                "url": url,
                "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                "description": description,
            },
            timeout=30,
        )
        st.write(response.json())

st.subheader("Ask")
question = st.text_input("Question")
artifact_type = st.selectbox(
    "Artifact type", ["summary", "faq", "comparison", "study_guide", "implementation_notes"]
)
if st.button("Ask NotebookLM"):
    response = requests.post(
        f"{API_BASE}/ask",
        json={"question": question, "artifact_type": artifact_type},
        timeout=60,
    )
    st.json(response.json())
