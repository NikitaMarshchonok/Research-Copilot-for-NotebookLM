from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from typing import Any, List

from app.core.exceptions import IntegrationError


class NotebookLMAnswer:
    def __init__(self, answer: str, sources: List[str] | None = None, raw: Any = None) -> None:
        self.answer = answer
        self.sources = sources or []
        self.raw = raw


class NotebookLMClient(ABC):
    @abstractmethod
    def ask(self, notebook_url: str, question: str) -> NotebookLMAnswer:
        raise NotImplementedError


class StubNotebookLMClient(NotebookLMClient):
    def ask(self, notebook_url: str, question: str) -> NotebookLMAnswer:
        answer = (
            "Stub response. Configure bridge mode to query NotebookLM MCP.\n\n"
            f"Notebook: {notebook_url}\n"
            f"Question: {question}"
        )
        return NotebookLMAnswer(answer=answer, sources=[notebook_url], raw={"mode": "stub"})


class BridgeNotebookLMClient(NotebookLMClient):
    def __init__(self, command: str) -> None:
        self.command = command.strip()
        if not self.command:
            raise IntegrationError("NOTEBOOKLM_BRIDGE_COMMAND is empty.")

    def ask(self, notebook_url: str, question: str) -> NotebookLMAnswer:
        payload = {"notebook_url": notebook_url, "question": question}
        try:
            process = subprocess.run(
                self.command,
                input=json.dumps(payload),
                text=True,
                shell=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise IntegrationError(f"Bridge command failed to start: {exc}") from exc

        if process.returncode != 0:
            bridge_error = ""
            try:
                maybe_error = json.loads(process.stdout or "{}")
                if isinstance(maybe_error, dict):
                    bridge_error = str(maybe_error.get("error", "")).strip()
            except json.JSONDecodeError:
                bridge_error = ""
            raise IntegrationError(
                "Bridge command failed.\n"
                f"bridge_error: {bridge_error}\n"
                f"stdout: {process.stdout}\n"
                f"stderr: {process.stderr}"
            )

        try:
            data = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            raise IntegrationError("Bridge command returned invalid JSON.") from exc

        return NotebookLMAnswer(
            answer=str(data.get("answer", "")),
            sources=list(data.get("sources", [])),
            raw=data.get("raw", data),
        )
