# Research Copilot for Cursor + NotebookLM

Local AI-assisted research tool for developers/analysts.

The project follows a **thin orchestration-layer** approach:

1. NotebookLM is the external knowledge engine.
2. This app orchestrates notebook registry, asks questions, runs research workflows.
3. Results are saved as local Markdown/JSON artifacts.

No custom RAG backend, no vector DB, no embeddings in MVP.

## Stack

- Python 3.11+
- Typer (CLI)
- FastAPI (API layer)
- Pydantic v2 (typed models)
- pytest
- Streamlit (minimal UI for stage 3)

## Project structure

```text
research-copilot/
├── .cursor/
│   └── mcp.json
├── app/
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_notebooks.py
│   │   └── routes_research.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logger.py
│   ├── models/
│   │   ├── export.py
│   │   ├── notebook.py
│   │   ├── query.py
│   │   └── report.py
│   ├── services/
│   │   ├── export_service.py
│   │   ├── notebook_registry.py
│   │   ├── notebooklm_client.py
│   │   ├── prompt_templates.py
│   │   └── research_service.py
│   ├── storage/
│   │   ├── file_store.py
│   │   └── json_store.py
│   ├── bootstrap.py
│   ├── cli.py
│   ├── main.py
│   └── ui.py
├── data/
│   ├── history.json
│   └── notebooks.json
├── outputs/
│   └── .gitkeep
├── tests/
│   ├── test_exports.py
│   ├── test_health.py
│   └── test_registry.py
├── .env.example
├── .gitignore
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## Setup on macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.cli init
```

## CLI commands

Show help:

```bash
python -m app.cli --help
```

Notebook registry:

```bash
python -m app.cli notebooks list
python -m app.cli notebooks add --name "AI Agents" --url "https://notebooklm.google.com/notebook/..."
python -m app.cli notebooks select <NOTEBOOK_ID>
```

Ask one question:

```bash
python -m app.cli ask --question "What are main trade-offs?" --artifact-type summary
```

Run research mode:

```bash
python -m app.cli research \
  --topic "MCP for research automation" \
  --question "What is MCP?" \
  --question "What are risks of unofficial integrations?" \
  --artifact-type study_guide
```

Export by history id:

```bash
python -m app.cli export --history-id <ASK_OR_RESEARCH_ID>
```

Artifacts are written into `outputs/`.

## FastAPI

Run server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /health`
- `GET /notebooks`
- `POST /notebooks`
- `POST /notebooks/select`
- `POST /ask`
- `POST /research`
- `POST /export` (alias: `POST /exports`)

Open docs: <http://127.0.0.1:8000/docs>

## Minimal UI (Stage 3)

```bash
streamlit run app/ui.py
```

The UI is intentionally minimal and uses the local FastAPI backend.

## NotebookLM MCP in Cursor

Add `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp@latest"]
    }
  }
}
```

After saving:

1. Restart Cursor (or reload window).
2. Verify MCP server is visible in Cursor tools.
3. Authenticate notebooklm-mcp when prompted.

## About NotebookLM integration in this MVP

This repository includes two connector modes:

- `stub` (default): fully local placeholder answer (safe for first run and demos).
- `bridge`: call a custom command that talks to NotebookLM MCP and returns JSON.

Configure bridge mode in `.env`:

```env
NOTEBOOKLM_CONNECTOR_MODE=bridge
NOTEBOOKLM_BRIDGE_COMMAND=python scripts/notebooklm_bridge.py
```

Bridge contract:

- stdin JSON: `{"notebook_url":"...","question":"..."}`
- stdout JSON: `{"answer":"...","sources":["..."],"raw":{...}}`

## Testing

```bash
pytest
```

## Security notes

- Do not commit `.env`.
- Do not commit local auth/session files.
- Use a dedicated Google account for browser-based automation where possible.
