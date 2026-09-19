# NeuroAI — monorepo buyruqlari (TZ §9.1: make dev / test / seed / worker)
# Root .env bitta manba (ADR-005): quyida o'qiladi va barcha bola jarayonlarga eksport qilinadi.
SHELL := /bin/bash
.DEFAULT_GOAL := help

-include .env
export

API_PORT      ?= 8000
WEB_PORT      ?= 3000
WORKER_PORT   ?= 8001
POSTGRES_PORT ?= 5433

API_DIR    := apps/api
WEB_DIR    := apps/web
WORKER_DIR := apps/ai_worker
UV   := uv
PNPM := pnpm

.PHONY: help install env db-up db-down dev dev-api dev-web dev-docker down logs \
        test test-api test-worker lint lint-py lint-web format migrate migration \
        seed worker health gen-types clean

help: ## Buyruqlar ro'yxati
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(firstword $(MAKEFILE_LIST)) | sort | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ---------- o'rnatish ----------
env: ## .env yo'q bo'lsa .env.example dan nusxa oladi
	@test -f .env || { cp .env.example .env; echo ".env yaratildi (.env.example dan) — portlarni tekshiring"; }

install: env ## Barcha bog'liqliklar: pnpm workspace + uv (api, ai_worker)
	$(PNPM) install
	cd $(API_DIR) && $(UV) sync
	cd $(WORKER_DIR) && $(UV) sync

# ---------- dev ----------
db-up: ## Docker'da postgres (daemon bo'lmasa o'tkazib yuboradi)
	@if docker info >/dev/null 2>&1; then \
		docker compose up -d postgres; \
	else \
		echo "⚠  Docker ishlamayapti — postgres o'tkazib yuborildi. DATABASE_URL=sqlite+aiosqlite:///./dev.db bilan ishlash mumkin."; \
	fi

db-down: ## Docker postgres'ni to'xtatish
	docker compose stop postgres

dev: env db-up ## Postgres (docker) + API (uvicorn --reload) + Web (next dev) — Ctrl-C hammasini to'xtatadi
	@echo "API  → http://localhost:$(API_PORT)/api/v1/health"
	@echo "Web  → http://localhost:$(WEB_PORT)"
	$(MAKE) -j2 dev-api dev-web

dev-api: ## Faqat API (port $(API_PORT))
	cd $(API_DIR) && $(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port $(API_PORT)

dev-web: ## Faqat Web (port $(WEB_PORT))
	$(PNPM) --filter web dev -p $(WEB_PORT)

worker: ## ai_worker skeleti lokalda (port $(WORKER_PORT)); real modellar — ofis GPU (docs/AI_WORKER_TZ.md)
	cd $(WORKER_DIR) && $(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port $(WORKER_PORT)

dev-docker: env ## Hammasi docker'da: web + api + postgres
	docker compose up --build

down: ## Docker stack'ni to'xtatish
	docker compose down

logs: ## Docker loglar
	docker compose logs -f --tail=100

# ---------- sifat ----------
test: test-api test-worker ## Barcha testlar (pytest)

test-api: ## API testlari
	cd $(API_DIR) && $(UV) run pytest -q

test-worker: ## ai_worker skeleti testlari
	cd $(WORKER_DIR) && $(UV) run pytest -q

lint: lint-py lint-web ## ruff + black --check + eslint + tsc + prettier --check

lint-py:
	cd $(API_DIR) && $(UV) run ruff check . && $(UV) run black --check .
	cd $(WORKER_DIR) && $(UV) run ruff check . && $(UV) run black --check .

lint-web:
	$(PNPM) --filter @neuroai/shared typecheck
	$(PNPM) --filter web lint
	$(PNPM) --filter web typecheck
	$(PNPM) --filter web format:check
	$(PNPM) format:check

format: ## black + ruff --fix + prettier --write
	cd $(API_DIR) && $(UV) run black . && $(UV) run ruff check --fix .
	cd $(WORKER_DIR) && $(UV) run black . && $(UV) run ruff check --fix .
	$(PNPM) --filter web format
	$(PNPM) format

# ---------- DB ----------
migrate: ## alembic upgrade head
	cd $(API_DIR) && $(UV) run alembic upgrade head

migration: ## Yangi migratsiya: make migration m="users_patients"
	@test -n "$(m)" || { echo 'm="nom" bering: make migration m="init"'; exit 1; }
	cd $(API_DIR) && $(UV) run alembic revision --autogenerate -m "$(m)"

seed: ## Demo akkauntlar va kontent (T-02+)
	cd $(API_DIR) && $(UV) run python scripts/seed.py

demo: seed ## "Bobur aka" 14 kunlik demo ma'lumotlari (T-17)
	cd $(API_DIR) && $(UV) run python scripts/demo_data.py

pregen-tts: ## Statik matnlar (mashq, ishora, yuz, xavfsiz skript) uchun TTS keshini to'ldirish
	cd $(API_DIR) && $(UV) run python scripts/pregen_tts.py --concurrency 1

# ---------- yordamchi ----------
health: ## API va worker health'ni curl qiladi
	@curl -sS http://localhost:$(API_PORT)/api/v1/health && echo
	@curl -sS http://localhost:$(API_PORT)/api/v1/health/providers && echo
	@curl -sS http://localhost:$(WORKER_PORT)/health && echo || true

gen-types: ## OpenAPI → packages/shared TS tiplari (API ishlab turishi kerak)
	API_OPENAPI_URL=http://localhost:$(API_PORT)/openapi.json $(PNPM) --filter @neuroai/shared generate

clean: ## Build artefaktlari va keshlar
	rm -rf $(WEB_DIR)/.next $(WEB_DIR)/public/sw.js $(API_DIR)/.pytest_cache $(API_DIR)/.ruff_cache \
		$(WORKER_DIR)/.pytest_cache $(WORKER_DIR)/.ruff_cache
	find . -name __pycache__ -type d -prune -not -path '*/node_modules/*' -not -path '*/.venv/*' -exec rm -rf {} +
