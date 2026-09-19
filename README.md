# NeuroAI

Insultdan keyingi bemorlar uchun **24/7 o'zbek tilidagi multimodal reabilitatsiya hamrohi**:
suhbatdosh, bemor ↔ oila tarjimoni, logoped protokoli bo'yicha kunlik mashqlar (nutq, yuz, kognitiv),
yuz simmetriyasi va kayfiyat kuzatuvi, qizil bayroqlar, klinisist paneli va parvarishchi ilovasi.

> NeuroAI vrachning o'rnini bosmaydi — tashxis qo'ymaydi, dori o'zgartirmaydi.
> U protokolni **bajartiradi**, **o'lchaydi** va **xabar beradi**. Klinik qarorlar — vrach tomonidan.

Hujjatlar: [docs/TZ.md](docs/TZ.md) (texnik topshiriq), [CLAUDE.md](CLAUDE.md) (kod qoidalari),
[docs/adr/](docs/adr/README.md) (qarorlar).

## Tuzilma

```
apps/web         Next.js 15 · TypeScript · Tailwind v4 · shadcn/ui · PWA (@serwist/next)
apps/api         FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic v2 — Python 3.12 (uv)
apps/ai_worker   GPU worker skeleti (STT/TTS/ovoz hissiyoti) — real modellar ofis kompyuterida
packages/shared  OpenAPI'dan generatsiya qilinadigan TS tiplar
docker-compose.yml (web, api, postgres) · Makefile · .env.example
```

## Tez boshlash

Talablar: Node ≥ 20 + pnpm 9, Python 3.12 (`uv` o'zi o'rnatadi), Docker (postgres uchun; ixtiyoriy).

```bash
make install        # pnpm install + uv sync (api, ai_worker); .env yo'q bo'lsa yaratadi
make dev            # postgres (docker) + API + Web
```

| Nima                | Manzil                                                         |
| ------------------- | -------------------------------------------------------------- |
| Web                 | http://localhost:3000                                          |
| API health          | http://localhost:8000/api/v1/health (yoki `/health`)           |
| API docs            | http://localhost:8000/docs                                     |
| Provayderlar holati | http://localhost:8000/api/v1/health/providers · web: `/status` |

Portlar band bo'lsa `.env`da `API_PORT`, `WEB_PORT`, `POSTGRES_PORT` ni o'zgartiring va
`NEXT_PUBLIC_API_URL` ni moslang ([ADR-005](docs/adr/ADR-005-ports-and-env.md)); `CORS_ORIGINS` bo'sh
qolsa `WEB_PORT` dan o'zi olinadi (tunnel/telefon uchun to'ldiring).
Docker bo'lmasa: `DATABASE_URL=sqlite+aiosqlite:///./dev.db`.

Hammasi docker'da: `make dev-docker` (keyin `make down`).

## Buyruqlar

| Buyruq                                       | Vazifa                                                       |
| -------------------------------------------- | ------------------------------------------------------------ |
| `make dev` / `make dev-api` / `make dev-web` | Dev serverlar                                                |
| `make worker`                                | `ai_worker` skeleti (port 8001) — modellar laptopda **yo'q** |
| `make test`                                  | pytest (api, ai_worker)                                      |
| `make lint` / `make format`                  | ruff + black · eslint + tsc + prettier                       |
| `make migrate` / `make migration m="nom"`    | Alembic                                                      |
| `make seed`                                  | Demo akkauntlar va kontent (T-02+)                           |
| `make health`                                | Health endpointlarni curl qiladi                             |
| `make gen-types`                             | OpenAPI → `packages/shared`                                  |

## AI worker (muhim)

Laptopda **hech qanday ML model o'rnatilmaydi**. `apps/ai_worker` — ofis GPU kompyuterida
(`docs/AI_WORKER_TZ.md`) ishlaydigan servis; ngrok orqali `AI_WORKER_URL` bilan ulanadi.
Worker tayyor bo'lguncha `AI_WORKER_URL=mock` — API to'liq ishlaydi (STT → "salom", TTS → jimlik, emotion → neytral).
Worker/bulut provayderlari uzilsa `FallbackChain` (Gemini/OpenAI) davom ettiradi ([ADR-001](docs/adr/ADR-001-fallback-chain.md)).

## Ticket holati (TZ §9.4)

| #           | Ticket                                                                                                  | Holat |
| ----------- | ------------------------------------------------------------------------------------------------------- | ----- |
| T-01        | Monorepo skaffold, docker-compose, Makefile, `.env.example`, lint/format, `GET /health`                 | ✅    |
| T-02        | DB modellar + Alembic + seed skeleti                                                                    | ⏳    |
| T-03 … T-19 | Auth, provayderlar, companion, yuz, mashqlar, tarjimon, xavfsizlik, protokol, panel, parvarishchi, demo | ⏳    |

## Litsenziya

Hakaton loyihasi (National AI Hackathon, Xorazm, 2026). Modellar va litsenziyalar: `docs/MODELS.md` (T-05+).
