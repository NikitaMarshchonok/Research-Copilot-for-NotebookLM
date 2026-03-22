#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Research Copilot Go-Live Check =="
echo

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
  PYTEST=".venv/bin/pytest"
else
  PYTHON="python3"
  PYTEST="pytest"
fi

echo "1) Running environment doctor..."
"$PYTHON" -m app.cli doctor
echo

echo "2) Running focused smoke tests..."
"$PYTEST" tests/test_snapshot_e2e_smoke.py tests/test_snapshot_api_extended.py -q
echo

cat <<'EOF'
3) Manual go-live verification (recommended):
   - Start API:
       uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   - Start UI:
       streamlit run app/ui.py
   - In UI run:
       ask -> snapshots create (x2+) -> snapshots update-pack

4) Optional real NotebookLM bridge validation:
   - Set in .env:
       NOTEBOOKLM_CONNECTOR_MODE=bridge
       NOTEBOOKLM_BRIDGE_COMMAND=python scripts/notebooklm_bridge.py
   - Then run:
       python -m app.cli doctor
       echo '{"notebook_url":"https://notebooklm.google.com/notebook/...","question":"Give me a short summary"}' | python scripts/notebooklm_bridge.py
EOF

echo
echo "Go-live check completed."
