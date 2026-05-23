.PHONY: dev start test lock sync

dev:
	uv run uvicorn app.main:app --reload

start:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	uv run pytest -v

lock:
	uv lock

sync:
	uv sync
