# Developer commands for this repo. Run them from the repo root; `make help` lists them.
# They work on the code in fde-impromptu-coach/ and never touch ~/FDE-Impromptu or launchd.
# GNU Make 3.81 compatible (the macOS default).

SHELL := /bin/bash
SKILL := fde-impromptu-coach
# The Mac's venv has the dependencies (python-pptx, Pillow, ...); elsewhere use python3 or PYTHON=...
PYTHON ?= $(shell if [ -x "$$HOME/FDE-Impromptu/venv/bin/python" ]; then echo "$$HOME/FDE-Impromptu/venv/bin/python"; else echo python3; fi)
LOG ?= $(CURDIR)/.test-output.log
PY39_VENV ?= $(CURDIR)/.venv-py39

.PHONY: help test test-one py39 sandbox

help:
	@echo "make test                  the whole suite, dry-run, once; full output in .test-output.log"
	@echo "make test-one T=stage      one module (scripts/tests/test_stage.py)"
	@echo "make py39                  the whole suite under Python 3.9 (needs uv)"
	@echo "make sandbox ARGS='stage status --json' [NOW=2026-11-07T08:00:00] [ANSWERS='Start now,Later']"
	@echo "                           one fde-coach command in a throw-away dry-run home"
	@echo "Python: $(PYTHON) (override with PYTHON=...)"

# One run: the failing tests and the summary on screen, everything else (tracebacks) in $(LOG).
test:
	@cd $(SKILL) && FDE_COACH_DRYRUN=1 "$(PYTHON)" -m unittest discover -s scripts/tests > "$(LOG)" 2>&1; \
	status=$$?; \
	grep -E '^(ERROR|FAIL):' "$(LOG)" || true; \
	tail -n 3 "$(LOG)"; \
	echo "Full output, tracebacks included: $(LOG)"; \
	exit $$status

test-one:
	@if [ -z "$(T)" ]; then echo "usage: make test-one T=stage   (runs scripts/tests/test_stage.py)"; exit 2; fi
	@cd $(SKILL) && FDE_COACH_DRYRUN=1 "$(PYTHON)" -m unittest discover -s scripts/tests -p "test_$(T).py" -v

py39:
	@command -v uv >/dev/null 2>&1 || { echo "make py39 needs uv (https://docs.astral.sh/uv/), or run: make test PYTHON=python3.9"; exit 2; }
	@if [ ! -x "$(PY39_VENV)/bin/python" ]; then \
	  uv python install -q 3.9 && uv venv -q -p 3.9 "$(PY39_VENV)" && \
	  uv pip install -q -p "$(PY39_VENV)/bin/python" -r $(SKILL)/requirements.txt; \
	fi
	@$(MAKE) --no-print-directory test PYTHON="$(PY39_VENV)/bin/python"

sandbox:
	@if [ -z "$(ARGS)" ]; then echo "usage: make sandbox ARGS='stage status --json' [NOW=...] [ANSWERS=...]"; exit 2; fi
	@PYTHON="$(PYTHON)" bash $(SKILL)/scripts/tools/sandbox.sh $(ARGS)
