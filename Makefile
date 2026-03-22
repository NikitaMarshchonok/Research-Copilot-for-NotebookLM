PYTHON ?= python3
UVICORN ?= uvicorn

.PHONY: install dev test test-snapshots-smoke preflight doctor go-live-check run-api run-cli init-data

install:
	$(PYTHON) -m pip install -r requirements.txt

dev:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	pytest

test-snapshots-smoke:
	pytest tests/test_snapshot_e2e_smoke.py tests/test_snapshot_api_extended.py -q

doctor:
	$(PYTHON) -m app.cli doctor

preflight:
	$(PYTHON) -m app.cli doctor
	pytest

go-live-check:
	bash scripts/go_live_demo.sh

run-api:
	$(UVICORN) app.main:app --reload --host 127.0.0.1 --port 8000

run-cli:
	$(PYTHON) -m app.cli --help

init-data:
	$(PYTHON) -m app.cli init
