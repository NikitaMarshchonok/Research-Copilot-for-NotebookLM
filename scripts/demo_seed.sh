#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
TAG="demo-${STAMP}"
VIEW_NAME="demo-view-${STAMP}"
NOTEBOOK_NAME="Demo Notebook ${STAMP}"
NOTEBOOK_URL="https://notebooklm.google.com/notebook/${STAMP}"

echo "== Demo Seed =="
echo "tag: ${TAG}"
echo "view: ${VIEW_NAME}"
echo

"$PYTHON" -m app.cli init

ADD_OUT="$("$PYTHON" -m app.cli notebooks add --name "$NOTEBOOK_NAME" --url "$NOTEBOOK_URL" --tags "$TAG" --description "Auto demo seed")"
NOTEBOOK_ID="$(echo "$ADD_OUT" | awk -F': ' '/Added notebook:/ {print $2}' | tr -d '[:space:]')"
if [[ -z "${NOTEBOOK_ID}" ]]; then
  echo "Could not parse notebook id from output:"
  echo "$ADD_OUT"
  exit 1
fi

"$PYTHON" -m app.cli notebooks select "$NOTEBOOK_ID"
"$PYTHON" -m app.cli views add --name "$VIEW_NAME" --scope history --type ask --tag "$TAG" --description "Demo generated view"

"$PYTHON" -m app.cli ask --question "What is MCP and why is it useful?" --artifact-type summary --tag "$TAG"
"$PYTHON" -m app.cli snapshots create --view "$VIEW_NAME"

"$PYTHON" -m app.cli ask --question "List practical risks for unofficial NotebookLM automation." --artifact-type faq --tag "$TAG"
"$PYTHON" -m app.cli snapshots create --view "$VIEW_NAME"

"$PYTHON" -m app.cli ask --question "Give implementation notes for a research workflow." --artifact-type implementation_notes --tag "$TAG"
"$PYTHON" -m app.cli snapshots create --view "$VIEW_NAME"

echo
echo "Latest brief:"
"$PYTHON" -m app.cli snapshots diff-latest-brief --view "$VIEW_NAME" --top 5

echo
echo "Update pack export:"
"$PYTHON" -m app.cli snapshots update-pack-export --view "$VIEW_NAME" --top 5 --trend-limit 8

echo
echo "Demo seed completed."
echo "Use this view in UI/API: ${VIEW_NAME}"
