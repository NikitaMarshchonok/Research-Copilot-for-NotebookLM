from __future__ import annotations


ARTIFACT_HINTS: dict[str, str] = {
    "summary": "Give a concise structured summary with key points.",
    "faq": "Answer as FAQ with short Q/A pairs.",
    "comparison": "Provide a comparison table-style answer with trade-offs.",
    "study_guide": "Create a study guide with concepts and checkpoints.",
    "implementation_notes": "Focus on practical implementation notes and risks.",
}


def build_question(question: str, artifact_type: str) -> str:
    hint = ARTIFACT_HINTS.get(artifact_type, ARTIFACT_HINTS["summary"])
    return f"{question}\n\nOutput format requirement: {hint}"
