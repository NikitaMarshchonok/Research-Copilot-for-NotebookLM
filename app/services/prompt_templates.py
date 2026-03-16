from __future__ import annotations


ARTIFACT_HINTS: dict[str, str] = {
    "summary": "Give a concise structured summary with key points.",
    "faq": "Answer as FAQ with short Q/A pairs.",
    "comparison": "Provide a comparison table-style answer with trade-offs.",
    "study_guide": "Create a study guide with concepts and checkpoints.",
    "implementation_notes": "Focus on practical implementation notes and risks.",
}


DEFAULT_RESEARCH_TEMPLATES: dict[str, dict[str, object]] = {
    "summary": {
        "description": "Quick source-grounded topic summary.",
        "artifact_type": "summary",
        "questions": [
            "What is {topic}?",
            "What are the key concepts and terminology of {topic}?",
            "What are the main practical takeaways about {topic}?",
        ],
    },
    "faq": {
        "description": "Generate a concise FAQ for a topic.",
        "artifact_type": "faq",
        "questions": [
            "What are the most common beginner questions about {topic}?",
            "What are typical misconceptions about {topic}?",
            "What edge cases or caveats should be in an FAQ about {topic}?",
        ],
    },
    "comparison": {
        "description": "Compare alternatives and trade-offs.",
        "artifact_type": "comparison",
        "questions": [
            "What are the major options/approaches related to {topic}?",
            "What are pros and cons of each option for {topic}?",
            "Which option is best for small teams vs enterprise cases in {topic}?",
        ],
    },
    "study_guide": {
        "description": "Structured study plan and checkpoints.",
        "artifact_type": "study_guide",
        "questions": [
            "What fundamentals should be learned first for {topic}?",
            "What is an effective learning path for {topic} from basic to advanced?",
            "What practical exercises can validate understanding of {topic}?",
        ],
    },
    "implementation_notes": {
        "description": "Implementation-oriented notes for engineers.",
        "artifact_type": "implementation_notes",
        "questions": [
            "What architecture patterns are recommended for {topic}?",
            "What integration risks and failure modes exist for {topic}?",
            "What checklist should be followed when implementing {topic} in production?",
        ],
    },
}


def build_question(question: str, artifact_type: str) -> str:
    hint = ARTIFACT_HINTS.get(artifact_type, ARTIFACT_HINTS["summary"])
    return f"{question}\n\nOutput format requirement: {hint}"
