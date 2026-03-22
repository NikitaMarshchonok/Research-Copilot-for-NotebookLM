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
│   │   ├── routes_research.py
│   │   └── routes_workspaces.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logger.py
│   ├── models/
│   │   ├── artifact.py
│   │   ├── bundle_preset.py
│   │   ├── export.py
│   │   ├── history.py
│   │   ├── notebook.py
│   │   ├── query.py
│   │   ├── report.py
│   │   ├── search_view.py
│   │   ├── snapshot.py
│   │   ├── template.py
│   │   └── workspace.py
│   ├── services/
│   │   ├── bundle_preset_service.py
│   │   ├── export_service.py
│   │   ├── notebook_registry.py
│   │   ├── notebooklm_client.py
│   │   ├── prompt_templates.py
│   │   ├── research_service.py
│   │   ├── search_view_service.py
│   │   ├── template_service.py
│   │   └── workspace_service.py
│   ├── storage/
│   │   ├── file_store.py
│   │   └── json_store.py
│   ├── bootstrap.py
│   ├── cli.py
│   ├── main.py
│   └── ui.py
├── data/
│   ├── history.json
│   ├── bundle_presets.json
│   ├── notebooks.json
│   ├── search_views.json
│   ├── snapshots.json
│   ├── templates.json
│   └── workspaces.json
├── outputs/
│   └── .gitkeep
├── scripts/
│   └── notebooklm_bridge.py
├── tests/
│   ├── test_artifacts.py
│   ├── test_bundle_presets.py
│   ├── test_bridge_client.py
│   ├── test_batch_template_endpoint.py
│   ├── test_exports.py
│   ├── test_health.py
│   ├── test_history.py
│   ├── test_notebooks_active.py
│   ├── test_registry.py
│   ├── test_search_views.py
│   ├── test_snapshots.py
│   ├── test_templates.py
│   ├── test_templates_endpoint.py
│   ├── test_workspace_service.py
│   └── test_workspaces_endpoint.py
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

Multi-project workspace support:

- default workspace uses root `data/` and `outputs/`
- named workspaces use `workspaces/<name>/data` and `workspaces/<name>/outputs`

## CLI commands

Show help:

```bash
python -m app.cli --help
python -m app.cli doctor
```

Notebook registry:

```bash
python -m app.cli notebooks list
python -m app.cli notebooks add --name "AI Agents" --url "https://notebooklm.google.com/notebook/..."
python -m app.cli notebooks select <NOTEBOOK_ID>
python -m app.cli notebooks active

python -m app.cli workspaces list
python -m app.cli workspaces create --name "client-a" --description "Client A research"
python -m app.cli workspaces select --name "client-a"
python -m app.cli workspaces current
```

Ask one question:

```bash
python -m app.cli ask --question "What are main trade-offs?" --artifact-type summary
python -m app.cli ask --question "What are main trade-offs?" --artifact-type summary --tag draft --tag intro
```

Run research mode:

```bash
python -m app.cli research \
  --topic "MCP for research automation" \
  --question "What is MCP?" \
  --question "What are risks of unofficial integrations?" \
  --artifact-type study_guide

python -m app.cli templates list
python -m app.cli templates add --name "tech-comparison" \
  --question "What is {topic}?" \
  --question "Compare top options for {topic}" \
  --artifact-type comparison

python -m app.cli research-template --topic "MCP tooling" --template comparison

python -m app.cli research-batch-template \
  --topic "MCP basics" \
  --topic "NotebookLM orchestration" \
  --template study_guide \
  --continue-on-error
```

Export by history id:

```bash
python -m app.cli export --history-id <ASK_OR_RESEARCH_ID>
python -m app.cli history list
python -m app.cli history list --type research --tag deep --query "MCP"
python -m app.cli history get <ASK_OR_RESEARCH_ID>
python -m app.cli artifacts list
python -m app.cli artifacts list --type research --tag deep --query "topic"
python -m app.cli artifacts latest --type batch_research --template summary --tag draft
python -m app.cli export-latest --type research --tag deep
python -m app.cli export-bundle --name article-pack

python -m app.cli bundles list
python -m app.cli bundles add --name "my-pack" --type research --type ask --description "for article draft"
python -m app.cli bundles delete --name "my-pack"

python -m app.cli views list
python -m app.cli views add --name "deep-research" --scope history --type research --tag deep --query "MCP"
python -m app.cli views run --name "deep-research"
python -m app.cli views delete --name "deep-research"

python -m app.cli snapshots create --view deep-research
python -m app.cli snapshots list --view deep-research
python -m app.cli snapshots get --id <SNAPSHOT_ID>
python -m app.cli snapshots diff --from <SNAPSHOT_ID_A> --to <SNAPSHOT_ID_B>
python -m app.cli snapshots diff-export --from <SNAPSHOT_ID_A> --to <SNAPSHOT_ID_B>
python -m app.cli snapshots diff-latest --view deep-research
python -m app.cli snapshots diff-latest-export --view deep-research
python -m app.cli snapshots diff-brief --from <SNAPSHOT_ID_A> --to <SNAPSHOT_ID_B> --top 5
python -m app.cli snapshots diff-latest-brief --view deep-research --top 5
python -m app.cli snapshots digest --view deep-research --view article-research --top 5
python -m app.cli snapshots digest-export --view deep-research --top 5 --include-missing
python -m app.cli snapshots trend --view deep-research --limit 8
python -m app.cli snapshots trend-export --view deep-research --limit 8
python -m app.cli snapshots update-pack --view deep-research --top 5 --trend-limit 8
python -m app.cli snapshots update-pack-export --view deep-research --top 5 --trend-limit 8
```

Artifacts are written into `outputs/`.

## FastAPI

Run server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /health`
- `GET /workspaces`
- `POST /workspaces`
- `POST /workspaces/select`
- `GET /workspaces/current`
- `GET /notebooks`
- `GET /notebooks/active`
- `POST /notebooks`
- `POST /notebooks/select`
- `POST /ask`
- `POST /research`
- `GET /templates`
- `POST /templates`
- `POST /research/template`
- `POST /research/batch-template`
- `GET /history` (optional query: `item_type`, `tag`, `query`)
- `GET /history/{history_id}`
- `GET /artifacts` (optional query: `item_type`, `template_name`, `tag`, `query`)
- `GET /artifacts/latest` (same optional filters)
- `POST /exports/latest` (body supports `item_type`, `template_name`, `tag`, `query`)
- `POST /exports/bundle` (bundle presets: `article-pack`, `tech-brief-pack`, `study-pack`)
- `GET /bundle-presets`
- `POST /bundle-presets`
- `DELETE /bundle-presets/{preset_name}`
- `GET /search-views`
- `POST /search-views`
- `DELETE /search-views/{view_name}`
- `GET /search-views/{view_name}/run`
- `POST /snapshots`
- `GET /snapshots`
- `GET /snapshots/{snapshot_id}`
- `POST /snapshots/diff`
- `POST /snapshots/diff/export`
- `GET /snapshots/diff/latest?view_name=...`
- `POST /snapshots/diff/latest/export?view_name=...`
- `POST /snapshots/diff/brief?top_items=5`
- `GET /snapshots/diff/latest/brief?view_name=...&top_items=5`
- `POST /snapshots/diff/digest`
- `POST /snapshots/diff/digest/export`
- `POST /snapshots/trend`
- `POST /snapshots/trend/export`
- `POST /snapshots/update-pack`
- `POST /snapshots/update-pack/export`
- `POST /export` (alias: `POST /exports`)

Open docs: <http://127.0.0.1:8000/docs>

## Minimal UI (Stage 3)

```bash
streamlit run app/ui.py
```

The UI is intentionally minimal and uses the local FastAPI backend.
It supports:

- notebook add/select
- ask and manual research
- template add/list
- template-based single research
- batch template research
- history view
- artifacts index with filters
- quick "latest artifact" lookup and export
- artifact bundle export for article/brief packs
- saved search views create/run/delete
- custom bundle presets per workspace
- history/artifact filtering by tags and search query
- saved search views per workspace
- materialized snapshots from saved views
- snapshot diff reports between two snapshots
- executive diff summary (net change/churn/retention) for article/TZ notes
- story-ready diff brief (1-line narrative + top changed IDs)
- weekly-style multi-view diff digest for research updates
- per-view trend timeline across last N snapshots
- one-shot update pack (latest brief + trend) per view

Optional API URL override for UI:

```bash
RESEARCH_COPILOT_API_BASE=http://127.0.0.1:8000 streamlit run app/ui.py
```

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
NOTEBOOKLM_MCP_COMMAND=npx -y notebooklm-mcp@latest
NOTEBOOKLM_MCP_ASK_TOOL=
NOTEBOOKLM_MCP_TIMEOUT_SECONDS=45
```

Bridge contract:

- stdin JSON: `{"notebook_url":"...","question":"..."}`
- stdout JSON: `{"answer":"...","sources":["..."],"raw":{...}}`

Quick local bridge check:

```bash
echo '{"notebook_url":"https://notebooklm.google.com/notebook/...","question":"Give me a short summary"}' \
  | python scripts/notebooklm_bridge.py
```

If the bridge cannot auto-detect the MCP tool name, set it explicitly in `.env`:

```env
NOTEBOOKLM_MCP_ASK_TOOL=<exact_tool_name_from_mcp_server>
```

## Testing

```bash
pytest
pytest tests/test_snapshot_e2e_smoke.py -q
make test-snapshots-smoke
make doctor
make preflight
make go-live-check
```

## Release checklist

Before final demo/hand-off:

1. `python -m app.cli doctor` returns all `OK`.
2. `make preflight` passes.
3. FastAPI starts and `/docs` opens.
4. Streamlit UI loads and can run `ask` and `snapshots update-pack`.
5. Bridge mode validated if you demo real NotebookLM (`NOTEBOOKLM_CONNECTOR_MODE=bridge`).

## 10-minute go-live flow

```bash
source .venv/bin/activate
python -m app.cli init
make go-live-check
make demo-seed
make final-demo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# new terminal
streamlit run app/ui.py
```

## Security notes

- Do not commit `.env`.
- Do not commit local auth/session files.
- Use a dedicated Google account for browser-based automation where possible.
