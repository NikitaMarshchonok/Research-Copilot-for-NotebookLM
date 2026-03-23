# Portfolio demo narrative (filled example)

This file is a **ready-to-publish** story for GitHub / CV / case study.  
It matches the automated flow in `scripts/demo_seed.sh` (tag `demo-<timestamp>`, view `demo-view-<timestamp>`).

> **Stub vs bridge:** below assumes `NOTEBOOKLM_CONNECTOR_MODE=stub` (default).  
> For a “real NotebookLM” portfolio story, switch to `bridge`, re-run the same flow, and replace the **Sample answer** + **brief** with your actual outputs.

---

## One-liner pitch

Research Copilot is a **local orchestration layer** over NotebookLM: it manages notebooks, runs structured research, exports Markdown/JSON artifacts, and tracks evolution via **snapshots, diffs, digests, and update packs** — without building a custom RAG stack.

---

## Context

| Item | Value |
|------|--------|
| **Workspace** | `default` (root `data/` + `outputs/`) |
| **Connector** | `stub` (safe demo; answers are deterministic placeholders) |
| **Goal** | Show an end-to-end research workflow + reproducible exports + snapshot analytics |

---

## Recorded run (automated)

This block is from an actual **`make final-demo`** execution in the repo (stub connector, default workspace).  
Re-run `make final-demo` anytime; filenames will change with a new timestamp — update this section if you want README to stay in sync.

| Field | Value |
|------|--------|
| **Date** | 2026-03-23 |
| **Tag** | `demo-20260323-224329` |
| **Saved view** | `demo-view-20260323-224329` |
| **Active notebook id** | `23321ee7-063a-49a0-8643-b32ef43a40f3` |

**Latest diff brief** (verbatim):

```text
View 'demo-view-20260323-224329' grew: 2 -> 3 (net +1), churn 50.0%, retention 66.7%; added 1, removed 0.
Top added: e906d709-8f35-432e-ae9f-7490df548561
Top removed: -
```

**Update pack export** (paths relative to repo root):

- `outputs/snapshot-update-pack-demo-view-20260323-224329-update-pack-20260323-204332.md`
- `outputs/snapshot-update-pack-demo-view-20260323-224329-update-pack-20260323-204332.json`

**Example `ask` exports** (same run):

- `outputs/answer-what-is-mcp-and-why-is-it-useful-20260323-204330.md`
- `outputs/answer-list-practical-risks-for-unofficial-notebooklm-automation-20260323-204331.md`
- `outputs/answer-give-implementation-notes-for-a-research-workflow-20260323-204331.md`

> Timestamps in filenames use UTC (`204330` etc.) while the demo tag uses local stamp (`224329`) — both come from the same run.

---

## How this run was produced (copy-paste)

```bash
source .venv/bin/activate
make final-demo
# or only seed:
# bash scripts/demo_seed.sh
```

The script prints:

- `tag: demo-YYYYMMDD-HHMMSS`
- `view: demo-view-YYYYMMDD-HHMMSS`

Use that **view name** in the UI (Snapshots / Update Pack) or in CLI:

```bash
python -m app.cli snapshots diff-latest-brief --view "demo-view-YYYYMMDD-HHMMSS" --top 5
python -m app.cli snapshots update-pack-export --view "demo-view-YYYYMMDD-HHMMSS" --top 5 --trend-limit 8
```

---

## Flow (what happened)

1. **Init** — ensured workspace data dirs and stores exist (`python -m app.cli init`).
2. **Notebook** — registered a demo NotebookLM URL and set it **active** (required for `ask`).
3. **Saved view** — created `history` scoped view filtered by `ask` + demo tag (only demo-tagged asks appear).
4. **Three asks** — each persisted to `history.json` and exported under `outputs/` (`answer-*.md` / `answer-*.json`).
5. **Three snapshots** — materialized the view after each ask; each snapshot stores the full item list + changelog vs previous snapshot.
6. **Analytics** — printed **latest diff brief** (story-ready sentence) and exported **update pack** (brief + trend table) to `outputs/`.

---

## Sample stub answer (what GitHub readers see in `outputs/`)

In stub mode, each `ask` produces an answer like:

```text
Stub response. Configure bridge mode to query NotebookLM MCP.

Notebook: https://notebooklm.google.com/notebook/<timestamp>
Question: <your question text>
```

Sources list includes the notebook URL. This is **intentional** for CI/portfolio demos; bridge mode swaps in grounded NotebookLM text.

---

## Sample latest diff brief (shape of output)

After the third snapshot, `snapshots diff-latest-brief` prints one line similar to:

```text
View 'demo-view-YYYYMMDD-HHMMSS' grew: 2 -> 3 (net +1), churn 33.3%, retention 66.7%; added 1, removed 0.
```

(Exact percentages depend on item counts; the **format** is stable.)

---

## Key outputs (where to find them)

Artifacts land in **`outputs/`** with timestamped names.

| Artifact | Typical filename pattern |
|----------|---------------------------|
| Single ask | `answer-*.md`, `answer-*.json` |
| Snapshot | `snapshot-*.md`, `snapshot-*.json` |
| Update pack | `snapshot-update-pack-demo-view-<stamp>-*.md` (+ matching `.json`) |

**Quick commands to grab the newest files after a run:**

```bash
ls -t outputs/snapshot-update-pack-*.md | head -3
ls -t outputs/snapshot-update-pack-*.json | head -3
ls -t outputs/answer-*.md | head -5
```

Replace the lines below with paths from *your* machine after `make final-demo`:

- **Update pack (Markdown):** `outputs/snapshot-update-pack-demo-view-<YOUR_STAMP>-<TIMESTAMP>.md`
- **Update pack (JSON):** `outputs/snapshot-update-pack-demo-view-<YOUR_STAMP>-<TIMESTAMP>.json`
- **Example ask (Markdown):** `outputs/answer-what-is-mcp-and-why-is-it-useful-<TIMESTAMP>.md` (slug may vary)

---

## Why it matters (portfolio bullets)

- **NotebookLM stays the knowledge engine** — no custom vector DB / embeddings in MVP; the repo shows orchestration, storage, and product surface (CLI + API + UI).
- **Research becomes traceable** — snapshots + diffs + update packs give a credible “how the corpus evolved” story for articles, specs, and weekly updates.
- **Shippable locally** — one-command demo (`make final-demo`), health check (`python -m app.cli doctor`), and pytest smoke coverage.

---

## Optional: bridge mode one-liner for “real” demo

```env
NOTEBOOKLM_CONNECTOR_MODE=bridge
NOTEBOOKLM_BRIDGE_COMMAND=python scripts/notebooklm_bridge.py
```

Then re-run `bash scripts/demo_seed.sh` and refresh the **Sample answer** and **Key outputs** sections with real grounded text and paths.

---

## Linking screenshots / GIF in README

Add files under `assets/` (see `assets/README.md`), then in root `README.md`:

```md
## Demo

![Flow](assets/demo-flow.gif)
```
