# ADR-003 — Monorepo toolchain: pnpm workspace + uv, Python 3.12, Makefile

**Sana:** 2026-09-19 · **Holat:** qabul qilingan (T-01)

## Kontekst

TZ §4.2/§9.1 monorepo (`apps/web`, `apps/api`, `apps/ai_worker`, `packages/shared`) va
`Makefile` ni belgilaydi, lekin paket menejerlarini aniq aytmaydi. Laptopda Node 24, pnpm 9,
Python 3.14 (tizim), `uv` bor. TZ backend uchun Python 3.12 deydi.

## Qaror

- **JS:** pnpm workspace (`pnpm-workspace.yaml`: `apps/web`, `packages/*`). Turborepo/Nx yo'q —
  solo dasturchi uchun ortiqcha; `Makefile` orkestratsiya qiladi.
- **Python:** `uv` (`pyproject.toml` + `uv.lock`) har app uchun alohida muhit;
  `.python-version = 3.12` (`uv python install 3.12`). Tizim Python 3.14 ishlatilmaydi
  (ba'zi kutubxonalarda 3.14 wheel'lari hali barqaror emas, TZ 3.12 deydi).
- **Buyruqlar:** `make install | dev | dev-docker | test | lint | format | migrate | migration | seed | worker`.
- `ai_worker` uchun `requirements.txt` ham saqlanadi (TZ) — ofis kompyuterida `pip`/conda bilan
  o'rnatiladi; laptopda faqat `fastapi`/`uvicorn` (skelet).

## Oqibatlar

- `pnpm install` root'da butun workspace'ni o'rnatadi; `packages/shared` web'ga `workspace:*` bilan ulanadi.
- CI (GitHub Actions) `uv sync` + `pnpm install --frozen-lockfile` bilan ishlaydi.
