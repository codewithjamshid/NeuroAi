# DEMO — ssenariy va chek-list (2026-09-19)

Manba: `docs/TZ.md` §11 (5–6 daqiqa), qisqartirilgan scope `docs/DEMO_SCOPE.md`.

## Ishga tushirish (laptop)

```bash
make dev          # postgres (docker :5433) + API :8010 + Web :3000   (portlar .env da)
make demo         # seed + "Bobur aka" 14 kunlik ma'lumot (idempotent)
make health       # API + worker health
```

- Web: http://localhost:3000 · Holat: http://localhost:3000/status · API docs: http://localhost:8010/docs
- Akkauntlar (parol `demo1234`): `bemor@demo.uz` (Bobur, 62), `qizi@demo.uz` (Nilufar, parvarishchi), `logoped@demo.uz` (Dilnoza, klinisist)
- Ikkinchi bemor: Gulnora Yusupova (klinisist ro'yxatida).

## Provayderlar (bugungi holat)

| Vazifa         | Birinchi                         | Zaxira                          | Izoh                                                |
| -------------- | -------------------------------- | ------------------------------- | --------------------------------------------------- |
| LLM            | OpenAI `gpt-4o-mini` (1.3–2.6 s) | Gemini `gemini-3-flash-preview` | Gemini bepul tarif: 20 so'rov/daq                   |
| STT            | Worker Kotib (ngrok)             | Gemini                          | Worker uzilsa 4 s ichida Gemini                     |
| TTS            | Worker Navoiy (ngrok, ~2–3.5 s)  | Brauzer `speechSynthesis`       | Gemini TTS 10/kun (o'chirilgan); OpenAI'da TTS yo'q |
| Ovoz hissiyoti | worker (`disabled`)              | null                            | Fusion ovozsiz ishlaydi                             |

`.env`: `AI_WORKER_URL`, `AI_WORKER_KEY` (ofis), `STT_PROVIDERS=worker,gemini,openai`, `TTS_PROVIDERS=worker,browser`.
Ovozli navbat o'lchovi: matn → javob + Navoiy audio ≈ 5.4 s (LLM 2.2 s + TTS 3.1 s); ovozli kirishda + STT (Kotib).

## Oqim (§11.2) → URL

1. **Hikoya (30 s)** — og'zaki.
2. **Klinisist (30 s):** `/d` → Bobur → **Protokol** → shablon `motor_aphasia_m1` → yaratish → bemor `/p` da "Bugungi reja".
3. **Suhbat + holat (60 s):** `bemor` → `/p/talk` → mikrofon → "Salom… bugun bog'imda…" → holat paneli (diqqat/charchoq/kayfiyat) + AI javobi. Mikrofon ishlamasa — matn maydoni.
4. **Tarjimon (60 s):** `/p/say` → "su… suv" → 3 karta → **Suv** → "Men suv ichmoqchiman." + oila izohi; 2-tabda `qizi` → `/c/say` (2 s polling) ko'rsatadi. Zaxira: **Taxta** (`/p/board`).
5. **Nutq mashqi (60 s):** `/p/exercise` → stimul → javob (ovoz/matn) → To'g'ri/Deyarli + ishora (semantik → fonemik → model) → 8/8 xulosa.
6. **Yuz mashqi (40 s):** `/p/exercise/face` → kamera → 10 s kalibrovka → tabassum ×5 → "Simmetriya NN %" jonli, takror hisoblagich. (Brauzer kamera ruxsati kerak; Chrome.)
7. **Xavfsizlik (40 s):** `/p/talk` → "hech narsaning foydasi yo'q, o'lsam yaxshi edi" → xavfsiz skript + **Yordam** tugmasi → Telegram (`@sonov1_bot`, parvarishchi `/start <kod>` bilan ulangan bo'lsa) → `/d` → **Bayroqlar** → "ko'rdim".
8. **Panel + hisobot (40 s):** `/d/patients/<Bobur>` → **Umumiy** (14 kun: aniqlik ↑, mustaqillik ↑, FSI 64→71 %, rioya 86 %) → **Hisobot** → generatsiya (15–25 s) → markdown.
9. **Kill-switch (20 s):** `/status` → ofisda ngrok'ni o'chirish → STT `worker` circuit `open` → Gemini davom etadi; suhbat ishlaydi.
10. **Yakun (20 s).**

## Demo oldidan chek-list

- [ ] `.env`: kalitlar, `AI_WORKER_URL` (ngrok), `NEXT_PUBLIC_API_URL` = API porti
- [ ] `make dev` → `/status` hammasi yashil; worker `online`
- [ ] `make demo` → `/d` da Bobur 14 kun grafik, 1 ta bayroq (resolved)
- [ ] Chrome: mikrofon + kamera ruxsati `localhost:3000` uchun berilgan
- [ ] Parvarishchi Telegram ulangan (`/c/settings` → kod → `/start <kod>`); test bayroq yuborib ko'rish
- [ ] Gemini kvota: demo oldidan 10 daqiqa Gemini'ga so'rov yubormaslik (20/daq)
- [ ] Zaxira: matnli kiritish (`/p/talk`, `/p/exercise`), Taxta (`/p/board`); zaxira video
- [ ] `git tag day-1` (oxirgi ishlaydigan holat)

## Ma'lum cheklovlar (halol aytiladi)

- Ovoz chiqishi brauzer TTS (o'zbek ovozi bo'lmasa — turk/standart); Navoiy worker'da tuzalgach almashadi.
- Yuz mashqi natijasi bazaga nisbatan; ovoz hissiyoti o'chirilgan (worker `voice_emotion: disabled`).
- PHQ, eslatmalar, kunlik Telegram xulosa, PIN rejimi — TZ P1/P2, "tez orada".
