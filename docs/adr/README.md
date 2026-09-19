# ADR — Architecture Decision Records

Qisqa qaror yozuvlari. Format: `ADR-NNN-slug.md` → **Kontekst / Qaror / Oqibatlar**.
TZ'da bo'lmagan har bir texnik qaror shu yerga yoziladi (CLAUDE.md qoidasi).

| #                                    | Qaror                                                                           | Holat          |
| ------------------------------------ | ------------------------------------------------------------------------------- | -------------- |
| [ADR-001](ADR-001-fallback-chain.md) | AI provayderlar: `FallbackChain` + circuit breaker (TZ §4.4)                    | qabul qilingan |
| [ADR-002](ADR-002-on-device-face.md) | Yuz/qo'l tahlili faqat brauzerda (MediaPipe), serverga metrika (TZ §1.4, §5.1)  | qabul qilingan |
| [ADR-003](ADR-003-toolchain.md)      | Monorepo toolchain: pnpm workspace + uv, Python 3.12, Makefile (turborepo yo'q) | qabul qilingan |
| [ADR-004](ADR-004-pwa-serwist.md)    | PWA: `@serwist/next` + Next.js `app/manifest.ts` (`next-pwa` o'rniga)           | qabul qilingan |
| [ADR-005](ADR-005-ports-and-env.md)  | Portlar `.env`da sozlanadi; docker postgres host'da 5433; bitta root `.env`     | qabul qilingan |
| [ADR-006](ADR-006-lint-format.md)    | Python: ruff (lint) + black (format); TS: eslint (next) + prettier              | qabul qilingan |
