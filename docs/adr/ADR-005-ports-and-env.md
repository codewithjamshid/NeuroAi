# ADR-005 — Portlar `.env`da sozlanadi; docker postgres host'da 5433; bitta root `.env`

**Sana:** 2026-09-19 · **Holat:** qabul qilingan (T-01)

## Kontekst

TZ standart portlari: web 3000, api 8000, worker 8001, postgres 5432. Dasturchi laptopida
8000 va 5432 boshqa loyiha (NAZAR-AI uvicorn + Postgres.app) tomonidan band.
Ilova D `DATABASE_URL=...@postgres:5432/...` — bu faqat docker tarmog'i ichida ishlaydi.

## Qaror

- Portlar `.env` orqali: `API_PORT`, `WEB_PORT`, `WORKER_PORT`, `POSTGRES_PORT`.
  `.env.example`da TZ standartlari (8000/3000/8001), lokal `.env`da bu laptop uchun `API_PORT=8010`.
- Docker postgres host'da **5433** portida chiqadi (lokal Postgres bilan to'qnashmaslik uchun);
  konteyner ichida 5432. `make dev` (api host'da) → `DATABASE_URL=...@localhost:5433/...`;
  `docker compose` api servisiga `environment:` orqali `@postgres:5432` beradi.
- **Bitta root `.env`**: Makefile (`set -a; . ./.env`), docker-compose (`env_file`),
  `apps/api` (`pydantic-settings`, `env_file=<root>/.env`) va `apps/web` (`NEXT_PUBLIC_*` process env)
  shu fayldan o'qiydi. `apps/ai_worker` o'z `.env`ini ham qo'llab-quvvatlaydi (ofis kompyuterida).
- `make dev` docker daemon bo'lmasa postgres'ni o'tkazib yuboradi (ogohlantirish);
  `DATABASE_URL=sqlite+aiosqlite:///./dev.db` bilan ishlash mumkin.

## Oqibatlar

- Boshqa loyiha jarayonlariga tegilmaydi.
- `NEXT_PUBLIC_API_URL` `API_PORT` bilan mos bo'lishi kerak (README'da eslatma).
- `CORS_ORIGINS` bo'sh bo'lsa API uni `WEB_PORT` dan hosil qiladi (`http://localhost:$WEB_PORT`,
  `http://127.0.0.1:$WEB_PORT`) — host `make dev` va compose bir xil ishlaydi; cloudflared/ngrok
  orqali telefon ulanganda tunnel domenini qo'lda qo'shish kerak.
