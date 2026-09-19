# ADR-004 — PWA: `@serwist/next` + Next.js `app/manifest.ts`

**Sana:** 2026-09-19 · **Holat:** qabul qilingan (T-01)

## Kontekst

TZ §4.2 `next-pwa` ni nomlaydi. Asl `next-pwa` (shadowwalker) 2022 dan beri yangilanmagan va
Next.js 15 App Router bilan muammoli. Uning fork'i `@ducanh2912/next-pwa` muallifi tomonidan
`@serwist/next` (Workbox asosida) foydasiga to'xtatilgan.

## Qaror

- Service worker: `@serwist/next` (v9, `next >= 14`), `src/app/sw.ts` → `public/sw.js`
  (gitignored, `next build`da generatsiya). Dev rejimda o'chirilgan (`disable: NODE_ENV === "development"`).
- Manifest: Next.js'ning tabiiy `src/app/manifest.ts` (`/manifest.webmanifest`), ikonkalar
  `public/icons/icon-{192,512}.png` (maskable), `theme-color` `viewport` orqali.
- `next dev`/`next build` webpack rejimida (Turbopack flag'siz) — Serwist webpack plugin.

## Oqibatlar

- Offline rejim (mashq kontenti + TTS keshi) P2 — `sw.ts`da runtime caching keyin qo'shiladi.
- Mikrofon/kamera uchun HTTPS kerak: `localhost` yoki `cloudflared` (TZ §4.1).
