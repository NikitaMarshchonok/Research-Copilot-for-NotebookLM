# Contributing

Thanks for your interest in this project.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.cli init
```

## Tests

```bash
pytest
make test-snapshots-smoke
make preflight
```

## Pull requests

- Keep changes focused on one concern per PR.
- Run `pytest` locally before opening a PR.
- Do not commit `.env`, local auth data, or generated files under `outputs/` (see `.gitignore`).

## NotebookLM / MCP

Integration with NotebookLM is **non-official** and may involve browser automation. Use a dedicated account where possible and read `SECURITY.md`.
