# apps/web — NeuroAI frontend

Next.js 15 (App Router, `src/`), TypeScript, Tailwind v4, shadcn/ui, PWA (`@serwist/next`, ADR-004).

## Ishga tushirish

Barcha buyruqlar `apps/web` ichida (yoki root'dan `pnpm --filter web <script>`):

| Buyruq                | Nima qiladi                                           |
| --------------------- | ----------------------------------------------------- |
| `pnpm dev -p 3000`    | dev server (webpack, SW o'chirilgan)                  |
| `pnpm build`          | prod build → `public/sw.js` + `.next/standalone`      |
| `pnpm start`          | prod server (`next start`)                            |
| `pnpm lint`           | eslint (next core-web-vitals + typescript + prettier) |
| `pnpm typecheck`      | `tsc --noEmit`                                        |
| `pnpm format[:check]` | prettier (+ tailwind plugin)                          |

Dependencies root'dan o'rnatiladi: `pnpm install` (workspace).

## Muhit

- `NEXT_PUBLIC_API_URL` — API manzili (default `http://localhost:8000/api/v1`). Next.js root
  `.env`ni o'qimaydi; Makefile uni process env orqali beradi (ADR-005). Bu laptopda
  `http://localhost:8010/api/v1`.
- `NEXT_PUBLIC_FACE_FPS` — MediaPipe kadr tezligi (T-07).
- `NEXT_PUBLIC_EMERGENCY_NUMBER` — "Yordam" tugmasi (`tel:`, default `103`). Root `.env`dagi
  `EMERGENCY_NUMBER` bilan **bir xil** bo'lishi shart (frontend build vaqtida inlayn qilinadi,
  backend'dagi qiymatni o'qiy olmaydi).

## Bemor UI (`/p/*`) — shrift qavati

`.patient-ui` (`src/app/globals.css`) asosiy shriftni 22px qiladi **va** Tailwind'ning
`--text-xs … --text-xl` o'zgaruvchilarini 22px ga qayta belgilaydi: shadcn primitivlari
(`Card` → `text-sm`, `CardTitle` → `text-base`, `Badge` → `text-xs`) rem'ga tayanadi va aks holda
14–16px'ga tushib ketadi. Natija: `/p/*` ichida `text-xs…text-xl` = 22px, `text-2xl`+ va
`text-[1.2em]` kabi aniq o'lchamlar o'z holicha. Yangi bemor ekranida kichik shrift kerak bo'lsa —
bu TZ §3 buzilishi; qavat olib tashlanmaydi. Avtomatik tekshiruv (Playwright, computed
`font-size ≥ 22px`) — T-18.

## Tuzilma

```
src/app            App Router: / (bosh), /status (ochiq), (patient)/p, (caregiver)/c, (clinician)/d
src/app/sw.ts      service worker (Serwist), src/app/manifest.ts → /manifest.webmanifest
src/features/<x>   api.ts / hooks.ts / components/   (namuna: features/health)
src/components     umumiy komponentlar; components/ui — shadcn
src/lib            api.ts (fetch o'rami, timeout 5 s, {error:{code,message}}), env.ts, i18n.ts
src/i18n/uz.json   barcha UI matnlari (kodda hardcode yo'q)
src/stores         Zustand (useUiStore — hand: left|right)
src/workers        audio / MediaPipe worker'lar (T-06, T-07)
```

## Docker

`apps/web/Dockerfile` — multi-stage, build context **repo root**:
`docker build -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=... .`
Build arg'lar: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_FACE_FPS`, `NEXT_PUBLIC_EMERGENCY_NUMBER`
(compose ularni root `.env`dan beradi). Standalone output: `.next/standalone/apps/web/server.js` (port 3000).

Kontekst filtri — faqat root `.dockerignore` (bitta manba). `apps/web` ichida `.dockerignore` yoki
`Dockerfile.dockerignore` **yaratilmaydi**: BuildKit `Dockerfile.dockerignore`ni root'dagidan ustun
qo'yadi va ikki fayl sinxron saqlanishi kerak bo'lib qoladi.
