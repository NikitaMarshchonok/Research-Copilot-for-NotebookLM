from __future__ import annotations

import json
import os
import queue
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any


def _extract_text_from_tool_result(result: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in result.get("content", []):
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())

    if chunks:
        return "\n\n".join(chunks)

    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        for key in ("answer", "response", "output", "text"):
            value = structured.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _extract_sources(result: dict[str, Any]) -> list[str]:
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        for key in ("sources", "citations", "references"):
            value = structured.get(key)
            if isinstance(value, list):
                return [str(item) for item in value]
    return []


def _read_stdin_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Bridge stdin is empty.")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Bridge stdin payload must be a JSON object.")
    return data


@dataclass
class MCPResponse:
    id: int
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class MCPStdioClient:
    def __init__(self, command: str, timeout_seconds: float = 30.0) -> None:
        self.command = command
        self.timeout_seconds = timeout_seconds
        self._next_id = 1
        self._responses: queue.Queue[MCPResponse] = queue.Queue()
        self._stop = threading.Event()
        self._process = self._spawn()
        self._reader = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader.start()

    def _spawn(self) -> subprocess.Popen[str]:
        args = shlex.split(self.command)
        return subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def _reader_loop(self) -> None:
        assert self._process.stdout is not None
        while not self._stop.is_set():
            line = self._process.stdout.readline()
            if line == "":
                return
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" not in message:
                continue
            response = MCPResponse(
                id=int(message["id"]),
                result=message.get("result"),
                error=message.get("error"),
            )
            self._responses.put(response)

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        assert self._process.stdin is not None
        self._process.stdin.write(json.dumps(payload) + "\n")
        self._process.stdin.flush()

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            remaining = max(0.01, deadline - time.monotonic())
            try:
                response = self._responses.get(timeout=remaining)
            except queue.Empty:
                continue
            if response.id != request_id:
                continue
            if response.error:
                raise RuntimeError(f"MCP error for {method}: {response.error}")
            return response.result or {}
        raise TimeoutError(f"Timeout waiting for MCP response: {method}")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        assert self._process.stdin is not None
        self._process.stdin.write(json.dumps(payload) + "\n")
        self._process.stdin.flush()

    def close(self) -> None:
        self._stop.set()
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def __enter__(self) -> "MCPStdioClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


def _guess_ask_tool(tools: list[dict[str, Any]]) -> str:
    explicit = os.getenv("NOTEBOOKLM_MCP_ASK_TOOL", "").strip()
    if explicit:
        return explicit

    candidates = []
    for tool in tools:
        name = str(tool.get("name", ""))
        lowered = name.lower()
        score = 0
        if "ask" in lowered or "question" in lowered or "query" in lowered:
            score += 2
        if "notebook" in lowered or "source" in lowered:
            score += 1
        if score > 0:
            candidates.append((score, name))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    raise RuntimeError(
        "Could not find an ask-like NotebookLM tool. "
        "Set NOTEBOOKLM_MCP_ASK_TOOL to a concrete tool name."
    )


def _build_argument_variants(notebook_url: str, question: str) -> list[dict[str, Any]]:
    return [
        {"notebook_url": notebook_url, "question": question},
        {"notebookUrl": notebook_url, "question": question},
        {"url": notebook_url, "question": question},
        {"notebook_url": notebook_url, "query": question},
        {"notebookUrl": notebook_url, "query": question},
        {"url": notebook_url, "query": question},
        {"notebook": notebook_url, "question": question},
        {"notebook": notebook_url, "query": question},
    ]


def run_bridge(notebook_url: str, question: str) -> dict[str, Any]:
    command = os.getenv("NOTEBOOKLM_MCP_COMMAND", "npx -y notebooklm-mcp@latest").strip()
    timeout_seconds = float(os.getenv("NOTEBOOKLM_MCP_TIMEOUT_SECONDS", "45"))

    with MCPStdioClient(command=command, timeout_seconds=timeout_seconds) as client:
        client.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "research-copilot-bridge", "version": "0.1.0"},
                "capabilities": {},
            },
        )
        client.notify("notifications/initialized")

        tools_result = client.request("tools/list", {})
        tools = tools_result.get("tools", [])
        if not isinstance(tools, list):
            raise RuntimeError("MCP tools/list returned invalid payload.")
        tool_name = _guess_ask_tool(tools)

        last_error: Exception | None = None
        tool_result: dict[str, Any] | None = None
        for arguments in _build_argument_variants(notebook_url, question):
            try:
                call_result = client.request(
                    "tools/call",
                    {"name": tool_name, "arguments": arguments},
                )
                if isinstance(call_result, dict):
                    tool_result = call_result
                    break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        if tool_result is None:
            raise RuntimeError(
                f"Failed to call tool '{tool_name}' with supported argument variants."
            ) from last_error

    answer = _extract_text_from_tool_result(tool_result)
    if not answer:
        answer = "NotebookLM returned no text answer."
    sources = _extract_sources(tool_result)
    return {"answer": answer, "sources": sources, "raw": tool_result}


def main() -> None:
    try:
        payload = _read_stdin_payload()
        notebook_url = str(payload.get("notebook_url", "")).strip()
        question = str(payload.get("question", "")).strip()
        if not notebook_url:
            raise ValueError("Field 'notebook_url' is required.")
        if not question:
            raise ValueError("Field 'question' is required.")
        result = run_bridge(notebook_url=notebook_url, question=question)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        error = {"error": str(exc)}
        print(json.dumps(error, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
