# @neuroai/shared — TS tiplar (OpenAPI'dan generatsiya)

`apps/api` FastAPI'ning `openapi.json` sxemasidan `openapi-typescript` bilan tiplar yaratiladi.
`apps/web` bu paketni `workspace:*` orqali ulaydi (ADR-003).

```ts
import type { HealthResponse, ApiError } from "@neuroai/shared"; // qo'lda yozilgan tiplar
import type { paths, components } from "@neuroai/shared/api"; // generatsiya qilingan OpenAPI tiplar
```

## Qayta generatsiya

API ishlab turganda, repo root'dan:

```bash
make gen-types
# yoki aniq URL bilan (pnpm root .env ni o'qimaydi — URL/portni o'zingiz bering):
API_OPENAPI_URL=http://localhost:8010/openapi.json pnpm --filter @neuroai/shared generate
```

`scripts/generate.mjs` portni taxmin qilmaydi: `API_OPENAPI_URL` yoki `API_PORT` (muhit, bo'lmasa
root `.env`) topilmasa to'xtaydi. Hujjat avval yuklab olinadi va `info.title` `NeuroAI API` bo'lmasa
(portda boshqa servis turgan bo'lsa) fayl yozilmaydi.

Natija: `src/generated/api.d.ts` (gitignored — har `make install`/`make dev`dan keyin yangilang).
Generatsiya qilinmagan bo'lsa `scripts/ensure-generated.mjs` (`postinstall`, `typecheck`) bo'sh
stub yozadi — paket va uni import qilgan `apps/web` baribir kompilyatsiya bo'ladi.

Tekshiruv: `pnpm --filter @neuroai/shared typecheck`.
