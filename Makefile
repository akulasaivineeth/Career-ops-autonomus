# Makefile — thin targets for human workflows (BUILD.md references `make oauth-gmail`).
.PHONY: help oauth-gmail bridge health

help:
	@echo "Targets:"
	@echo "  make oauth-gmail  — run Gmail OAuth helper (Task 0.5; requires client JSON outside repo)"
	@echo "  make bridge       — start FastAPI bridge on 127.0.0.1:8765"
	@echo "  make health       — curl local /health (bridge must be running)"

oauth-gmail:
	@echo "Stub: implement with \`uv run python -m agents.tools.gmail\` per BUILD.md Task 0.5"
	@exit 1

bridge:
	uv run python -m bridge

health:
	@curl -sf "http://127.0.0.1:8765/health" && echo
