# ADR-006 — Lint/format: ruff + black (Python), eslint + prettier (TS)

**Sana:** 2026-09-19 · **Holat:** qabul qilingan (T-01)

## Kontekst

TZ §9.5 `ruff/black/eslint/prettier` deydi. `ruff format` black bilan deyarli mos, lekin TZ black'ni nomlaydi.

## Qaror

- Python (`apps/api`, `apps/ai_worker`): `ruff check` (E, F, I, B, UP, ASYNC qoidalari, line-length 100)
  va `black` (line-length 100). `ruff format` ishlatilmaydi (ikki formatter bir-biriga zid bo'lmasin).
- TypeScript (`apps/web`): `eslint` (`eslint-config-next` + `eslint-config-prettier`) + `prettier`
  (`prettier-plugin-tailwindcss`). Root `prettier` md/yml/json uchun.
- `make lint` = ruff + black --check + eslint + tsc --noEmit; `make format` = black + ruff --fix + prettier --write.
- CI (`.github/workflows/ci.yml`) lint + test.

## Oqibatlar

- Commit oldidan `make lint && make test` (CLAUDE.md).
