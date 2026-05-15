# Makefile — developer shortcuts (see docs/ for full setup guides).
.PHONY: help oauth-gmail bridge dashboard health migrate sync-excel test lint

help:
	@echo ""
	@echo "  make bridge       — start bridge + dashboard on http://127.0.0.1:8765"
	@echo "  make dashboard    — open dashboard in browser (bridge must be running)"
	@echo "  make migrate      — apply pending SQLite migrations"
	@echo "  make sync-excel   — sync SQLite → data/applications.xlsx"
	@echo "  make oauth-gmail  — run Gmail OAuth flow (one-time)"
	@echo "  make health       — curl /health"
	@echo "  make test         — run pytest"
	@echo "  make lint         — ruff check + format"
	@echo ""

bridge:
	uv run python -m bridge

dashboard:
	@open http://127.0.0.1:8765 2>/dev/null || xdg-open http://127.0.0.1:8765

migrate:
	uv run python -m db.migrate

sync-excel:
	uv run python -c "from agents.tools.tracker import sync_from_db; n=sync_from_db(); print(f'Synced {n} rows')"

oauth-gmail:
	uv run python -m agents.tools.gmail

health:
	@curl -sf "http://127.0.0.1:8765/health" && echo

test:
	uv run pytest -q

lint:
	uv run ruff check agents bridge db && uv run ruff format --check agents bridge db
