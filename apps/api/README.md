# apps/api — NeuroAI backend

FastAPI + SQLAlchemy 2 (async) + Alembic + Pydantic v2, Python 3.12 via `uv`. All commands run
from this directory. Settings come from the root `.env` (ADR-005); with no `.env` the app boots
on SQLite + the mock worker.

```bash
uv sync                                   # .venv + uv.lock (dev deps included)
uv run uvicorn app.main:app --reload --port ${API_PORT:-8000}
uv run pytest -q                          # tests (httpx ASGITransport, mock worker)
uv run ruff check . && uv run black --check .   # lint
uv run black . && uv run ruff check --fix .     # format
uv run alembic upgrade head               # migrate (DATABASE_URL from .env)
uv run alembic revision --autogenerate -m "name"
uv run python scripts/seed.py             # T-02
```

Endpoints (T-01): `GET /health` (root alias), `GET /api/v1/health`, `GET /api/v1/health/providers`,
`GET /docs`. Errors: `{"error": {"code", "message"}}`. Every response echoes `X-Request-ID`.

Layout: `app/core` (config, logging, errors) · `app/api/{deps.py, v1/router.py}` (shared FastAPI deps; routers import these, never `app.ai.*`) · `app/modules/<name>/{router,service,schemas,models}.py`
· `app/ai/worker` (HTTP client + mock, `AI_WORKER_URL=mock`) · `app/ai/providers` (T-04) · `app/db` (Base, session)
· `alembic/` · `scripts/` · `tests/`.

Docker: `docker build -t neuroai-api .` — listens on 8000; map it to `API_PORT` in compose.
