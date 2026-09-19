# NeuroAI — Claude Code uchun loyiha qoidalari

Bu fayl `docs/TZ.md` (Texnik topshiriq v1.0) bilan birga o'qiladi. TZ — manba haqiqat;
bu yerda faqat kod yozishda har safar kerak bo'ladigan qoidalar takrorlanadi.
Qaror TZ'da bo'lmasa — eng oddiy ishlaydigan yechim tanlanadi va `docs/adr/` ga ADR yoziladi.

## Loyiha nima

Insultdan keyingi bemorlar uchun o'zbek tilidagi multimodal reabilitatsiya hamrohi
(suhbat, tarjimon, mashqlar, yuz simmetriyasi, xavfsizlik bayroqlari, klinisist paneli).
4 kunlik hakaton; ishlar `docs/TZ.md` §9.4 dagi T-01…T-19 ticket'lar bo'yicha ketma-ket bajariladi.

**Pozitsiya (har matnda):** NeuroAI vrachning o'rnini bosmaydi — tashxis qo'ymaydi, dori
o'zgartirmaydi, "davolayman" demaydi. U protokolni **bajartiradi**, **o'lchaydi**, **xabar beradi**.

## Qattiq cheklovlar

- **Bu laptop — ML model yo'q.** `whisper`, `faster-whisper`, `torch`, `transformers`, `funasr`,
  `mediapipe` (python) va boshqa og'ir ML kutubxonalarini **hech qachon** o'rnatma.
  `apps/ai_worker` ofis GPU kompyuterida alohida qilinadi (`docs/AI_WORKER_TZ.md`).
  Laptopda faqat worker HTTP klienti (`apps/api/app/ai/worker/client.py`) va
  `worker_mock` provayderi yoziladi; lokalda `AI_WORKER_URL=mock`.
- Video/kamera kadrlari serverga yuborilmaydi — faqat raqamli metrikalar (TZ §1.4, §5.1).
- Prompt va UI matnlarida tibbiy chegaralar (TZ §1.4, §6) buzilmaydi; `tests/test_prompts_guardrails.py`.
- Bu laptopda **8000** va **5432** portlari boshqa loyiha (NAZAR-AI) tomonidan band —
  o'sha jarayonlarni **o'ldirma**. NeuroAI portlari `.env` orqali sozlanadi
  (`API_PORT`, `WEB_PORT`, `POSTGRES_PORT`); lokal `.env`da `API_PORT=8010`.

## Repo tuzilmasi (TZ §9.1)

```
CLAUDE.md, docs/{TZ.md,AI_WORKER_TZ.md,adr/}   (MODELS.md — T-05+, DEMO.md — T-17: hali yo'q)
apps/web        Next.js 15 (App Router, src/), TS, Tailwind v4, shadcn/ui, PWA (@serwist/next)
apps/api        FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2 — Python 3.12 (uv)
apps/ai_worker  FastAPI skeleti (ofis GPU) — laptopda faqat stub/health
packages/shared TS tiplar (OpenAPI'dan generatsiya)
docker-compose.yml (web, api, postgres), Makefile, .env.example
```

## Toolchain

- Node 24 + **pnpm** (workspace: `pnpm-workspace.yaml`), Python **3.12** + **uv**
  (`apps/api/.python-version`, `apps/ai_worker/.python-version`).
- Buyruqlar: `make install`, `make dev` (postgres docker + api + web), `make test`, `make lint`,
  `make format`, `make migrate`, `make seed`, `make worker`, `make dev-docker`.
- Python: `ruff` (lint + import tartibi) + `black` (format). TS: `eslint` (next) + `prettier`.
- Git: har ticket alohida commit; kun oxirida `git tag day-N`.

## Kod qoidalari (TZ §9.3)

### Backend (`apps/api`)

- Modul = `app/modules/<name>/{router.py, service.py, schemas.py, models.py}`.
  Biznes mantiq faqat `service.py`; router faqat HTTP.
- AI provayderlar `app/ai/providers/<task>/` (`llm, stt, tts, voice_emotion, medllm`) —
  `Protocol` interfeys + implementatsiyalar + `FallbackChain`. **Router hech qachon provayderni to'g'ridan-to'g'ri chaqirmaydi.**
- Qatlamlar: router'lar FastAPI dependency'larni faqat `app/api/deps.py` dan oladi (`SettingsDep`, `WorkerDep`),
  `app.ai.*` ni import qilmaydi; `app/ai/*` esa `fastapi`ni import qilmaydi (`tests/test_layering.py` tekshiradi).
- Har LLM chaqiruvi: system prompt fayldan (`app/ai/prompts/*.md`), `response_schema` Pydantic,
  `temperature` va `timeout` aniq, natija `provider_calls` jadvaliga.
- Worker klienti har so'rovga `X-Worker-Key` **va** `ngrok-skip-browser-warning: 1` sarlavhalarini qo'shadi.
- API prefiksi `/api/v1`; xatolar `{"error": {"code", "message"}}`; sahifalash `?limit&offset`.
- DB: barcha jadvallar `id (uuid)`, `created_at`, `updated_at`; JSONB maydonlar Pydantic bilan validatsiya.
  Postgres asosiy, `sqlite+aiosqlite` bilan ham ishlashi shart.
- Sozlamalar faqat `app/core/config.py` (`pydantic-settings`, root `.env`). `os.environ` to'g'ridan-to'g'ri ishlatilmaydi.
- Loglar strukturlangan (JSON), `request-id`; PII loglarga tushmaydi.
- Testlar `apps/api/tests/`, `pytest` + `httpx.ASGITransport`; `scoring`, `fusion`, `safety`, `fallback` uchun birlik testlar majburiy.

### Frontend (`apps/web`)

- `src/features/<name>/{api.ts, hooks.ts, components/}`; audio va MediaPipe `src/workers/`; global holat Zustand (`session`, `state`, `audio`); server holat TanStack Query.
- Barcha UI matnlari `src/i18n/uz.json` (keyin `ru.json`) — kodda hardcode matn yo'q.
- Bemor UI (`/p/*`): shrift ≥ 22 px, tugmalar ≥ 64 px, yuqori kontrast, rangga tayanmaslik (ikonka + matn), "Yordam" tugmasi doim ko'rinadi.
- Layoutlar: `/p/*` bemor, `/c/*` parvarishchi, `/d/*` klinisist, `/status` ochiq sahifa.
- `NEXT_PUBLIC_API_URL` orqali API'ga murojaat; `fetch` o'rami `src/lib/api.ts`.

### Umumiy

- Tashqi chaqiruvlarda timeout majburiy. Har provayder chaqiruvi `provider_calls`ga.
- O'zgarishdan keyin: `make lint && make test` yashil bo'lishi shart.
- Har ticket oxirida: DoD tekshiruvi, qisqa hisobot, keyingi ticket rejasi.

## Hujjatlar

- `docs/TZ.md` — texnik topshiriq (§4 arxitektura, §4.6 API, §5 formulalar, §9 ish tartibi, Ilova A–E).
- `docs/adr/` — qisqa qaror yozuvlari (`ADR-NNN-slug.md`: Kontekst / Qaror / Oqibatlar).
