import sys
from pathlib import Path
from shlex import quote

from app.services.notebooklm_client import BridgeNotebookLMClient


def test_bridge_client_reads_json_response(tmp_path: Path) -> None:
    script = tmp_path / "bridge_echo.py"
    script.write_text(
        (
            "import json, sys\n"
            "payload = json.loads(sys.stdin.read())\n"
            "print(json.dumps({'answer': f\"ok: {payload['question']}\", 'sources': ['s1']}))\n"
        ),
        encoding="utf-8",
    )
    command = f"{quote(sys.executable)} {quote(str(script))}"
    client = BridgeNotebookLMClient(command=command)
    answer = client.ask("https://notebooklm.google.com/notebook/test", "hello")
    assert answer.answer == "ok: hello"
    assert answer.sources == ["s1"]
