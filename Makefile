PYTHON ?= python3
UVICORN ?= uvicorn

.PHONY: install dev test run-api run-cli init-data

install:
	$(PYTHON) -m pip install -r requirements.txt

dev:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	pytest

run-api:
	$(UVICORN) app.main:app --reload --host 127.0.0.1 --port 8000

run-cli:
	$(PYTHON) -m app.cli --help

init-data:
	$(PYTHON) -m app.cli init
