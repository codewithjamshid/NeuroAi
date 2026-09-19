# NeuroAI — texnik sharh (mentor/hakam savollari uchun)

_2026-09-19, National AI Hackathon, Xorazm. Manba hujjat: `docs/TZ.md`; demo ssenariysi: `docs/DEMO.md`._

## 1. Bir jumlada

NeuroAI — insultdan keyingi bemor uchun o'zbek tilida 24/7 ishlaydigan **multimodal reabilitatsiya hamrohi**: buzilgan nutq, yuz ifodasi va ovoz ohangidan bemorning holatini tushunadi, oilaga "tarjimon" bo'ladi, logoped belgilagan protokolni har kuni bajartiradi va o'lchaydi, xavfli holatlarda oila va vrachga xabar beradi. **Vrach o'rnini bosmaydi**: tashxis qo'ymaydi, dori o'zgartirmaydi — bajartiradi, o'lchaydi, xabar beradi.

## 2. Arxitektura (yuqori daraja)

```
Brauzer (Next.js PWA)                    Laptop (docker)                 Ofis GPU (RTX 3050, ngrok)
┌──────────────────────┐   HTTPS/JSON    ┌───────────────────┐  X-Worker-Key  ┌──────────────────────┐
│ Bemor / Parvarishchi │ ──────────────▶ │ FastAPI (api)     │ ─────────────▶ │ ai_worker (FastAPI)  │
│ / Klinisist UI       │ ◀────────────── │ auth, RBAC, DB    │ ◀───────────── │ /stt Kotib (Whisper) │
│ MediaPipe Face       │   wav/json      │ chains + fallback │                │ /tts Navoiy          │
│ (on-device, faqat    │                 │ safety, fusion    │  fallback      │ /voice-emotion (P1)  │
│  raqamli metrika)    │                 │ Telegram          │ ─────────────▶ │ /health              │
│ MediaRecorder + VAD  │                 │ PostgreSQL 16     │  Gemini/OpenAI └──────────────────────┘
└──────────────────────┘                 └───────────────────┘
```

- **Monorepo**: `apps/web` (frontend), `apps/api` (backend), `apps/ai_worker` (GPU servis), `packages/shared` (OpenAPI → TS tiplar), `docker-compose.yml` (web, api, postgres), `Makefile`.
- Laptopda **hech qanday ML model yo'q** — og'ir modellar ofis GPU kompyuterida; API unga HTTP orqali boradi; u uzilsa bulut zanjiri davom etadi.

## 3. Texnologiyalar

### Frontend — `apps/web`

| Nima                                                                         | Nega                                                                                                  |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Next.js 15.5** (App Router, `src/`), **React 19**, **TypeScript 5**        | Rol bo'yicha layoutlar (`/p` bemor, `/c` parvarishchi, `/d` klinisist), server/client komponentlar    |
| **Tailwind CSS v4** + **shadcn/ui** (base-ui)                                | Dizayn tokenlari (`globals.css`), bemor UI uchun font ≥ 22 px, tugmalar ≥ 64 px (`.patient-ui` floor) |
| **Zustand** (auth, audio holati), **TanStack Query** (server holat, polling) | `/c/say` 2 s polling; sessiya/holat keshi                                                             |
| **Recharts**                                                                 | Klinisist grafiklari (nutq aniqligi, mustaqillik, FSI, kayfiyat, rioya)                               |
| **@serwist/next** + `app/manifest.ts`                                        | PWA (o'rnatiladigan, service worker; TZ `next-pwa` o'rniga — ADR-004)                                 |
| **@mediapipe/tasks-vision** (FaceLandmarker)                                 | Brauzerda 478 nuqta + 52 blendshape — video serverga ketmaydi                                         |
| **MediaRecorder** (webm/opus) + energiya-VAD (AnalyserNode)                  | Tap-to-talk: 1.2 s jimlikda avtomatik to'xtash, maks 15 s                                             |
| **react-markdown**                                                           | AI haftalik hisobot (markdown)                                                                        |
| i18n: `src/i18n/uz.json` + typed `t()`                                       | Kodda hardcode matn yo'q; `ru.json` keyin                                                             |

### Backend — `apps/api` (Python 3.12, `uv`)

| Nima                                                       | Nega                                                                                                       |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **FastAPI 0.141** + **Pydantic v2** + `pydantic-settings`  | Async API, avtomatik OpenAPI, structured sozlamalar (`.env`)                                               |
| **SQLAlchemy 2.0 async** + **Alembic**                     | 26 jadval, UUID + timestamps, `JSONB` (Postgres) / `JSON` (SQLite) portativ; bitta boshlang'ich migratsiya |
| **PostgreSQL 16** (docker), SQLite fallback                | Solo dev ham docker'siz ishlaydi                                                                           |
| **PyJWT** (HS256, access 24 h / refresh 30 d) + **bcrypt** | Auth; RBAC `require_roles(...)` — 4 rol                                                                    |
| **httpx**                                                  | Worker klienti (`X-Worker-Key`, `ngrok-skip-browser-warning`), Telegram Bot API                            |
| **google-genai**, **openai** SDK                           | LLM/STT/TTS provayderlari, structured output (JSON schema)                                                 |
| **static-ffmpeg**                                          | webm/opus → 16 kHz mono wav (laptopda ffmpeg yo'q edi)                                                     |
| **rapidfuzz**                                              | CER (Levenshtein) — nutq mashqini ballash                                                                  |
| Strukturlangan JSON loglar + `X-Request-ID`                | Kuzatuv; `provider_calls` jadvali — har AI chaqiruv                                                        |
| **pytest** (311 test), **ruff** + **black**                | Scoring ≥ 30 holat, kalit so'zlar, prompt guardrail, fallback/circuit, auth matritsasi                     |

### AI worker — `apps/ai_worker` (ofis GPU)

- FastAPI; `POST /stt` — **Kotib/uzbek_stt_v1** (Whisper-medium, o'zbekcha fine-tune; CTranslate2 float16 orqali), `POST /tts` — **Navoiy TTS** (CosyVoice2-0.5B, o'zbek), `POST /voice-emotion` (emotion2vec — P1), `GET /health` (yuklangan modellar + GPU).
- **ngrok** static domain orqali laptopga ulanadi; laptopda `worker_mock` bilan API kalitsiz/worker'siz ham ishlaydi.

### Bulut AI

- **Gemini 2.5 Flash** (dialog, `thinking` o'chirilgan — 1.8 s), **gemini-3-flash-preview** (hisobot), **Gemini TTS** (`gemini-2.5-flash-preview-tts`), Gemini STT (audio kirish) — zaxira.
- **OpenAI gpt-4o-mini** — LLM zaxira (2.2 s).
- Hamma LLM chaqiruvi **structured output** (Pydantic sxema → JSON schema): `CompanionReply`, `InterpreterGuess`, `CoachVerdict`, `SessionSummary`, `Risk`.

### Infra / sifat

- `docker-compose.yml` (web, api, postgres), `Makefile` (`make dev/test/lint/demo/pregen-tts`), **pnpm workspace** + **uv**, GitHub Actions CI (ruff/black/pytest, eslint/tsc/prettier/build), ADR'lar `docs/adr/`.

## 4. Asosiy oqim: bitta ovozli navbat (`POST /sessions/{id}/messages`)

1. Brauzer: mikrofon → webm/opus (VAD avtomatik to'xtatadi) + oxirgi 10 s yuz metrikalari (`face_batch`) + javob kechikishi.
2. API: `ffmpeg` → wav 16 kHz → **STT zanjiri** (worker Kotib → Gemini → OpenAI) ∥ **ovoz hissiyoti** (worker, 2 s timeout, xato → null).
3. **Fusion** (`app/modules/state/fusion.py`, deterministik, TZ §5.4): yuz (diqqat, charchoq, ifoda), ovoz (valence/arousal), STT ishonchi, kayfiyat (o'zi), kechikish, kalit so'zlar → `PatientState {engagement, fatigue, mood, distress, explain[]}`.
4. **LLM** (`companion.md` prompt + bemor profili + holat JSON + bugungi reja + oxirgi 12 xabar) → `CompanionReply` JSON (`reply_text`, `tts_text`, `needs_confirmation`, `candidates`, `risk`, `suggested_action`).
5. **SafetyService**: LLM `risk` ⊕ o'zbekcha kalit so'zlar (lotin+kirill) → yuqorisi; `high` → javob **xavfsiz skript** bilan almashtiriladi, `red_flags` yoziladi (30 daqiqa dedup), **Telegram** parvarishchi + klinisistga, in-app xabar; dori savoli → "vrachingiz hal qiladi" + `notify_clinician`.
6. **TTS zanjiri** (Gemini → Navoiy → brauzer) → `media/tts/<sha1>.wav` kesh → `tts_url`.
7. Javob: bemor matni, AI matni + audio, kandidat kartalar, holat, xavf. UI: matn 28 px, kalit so'z qalin, avto-ijro.

O'lchangan kechikish (bugun): matn kirish → javob + Gemini audio ≈ 6–8 s (LLM 1.8 s + TTS 4–6 s); Navoiy bilan 5.4 s; keshlangan promptlar 0 s.

## 5. Modullar (backend `app/modules/*` ↔ frontend `features/*`)

| Modul                            | Nima qiladi                                                                                                                                                                  | Muhim detal                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `auth`, `users`                  | Login/refresh/`/me`, RBAC, demo akkauntlar                                                                                                                                   | 4 rol: patient, caregiver, clinician, admin                                  |
| `patients`                       | Bemor kartasi, rozilik (consent), kayfiyat, qizil bayroqlar + audit                                                                                                          | Kirish qoidalari: klinisist — o'zinikilar, parvarishchi — bog'langan         |
| `protocols`                      | Shablonlar (4), protokol elementlari, dorilar, **`/today`** rejasi, rioya                                                                                                    | Klinisist yaratadi → bemor ekranida "Bugungi reja"                           |
| `sessions`                       | Sessiya, xabarlar, transkript, yuz metrikalari, holat, xulosa (LLM)                                                                                                          | `PatientState` har xabarda saqlanadi                                         |
| `companion`                      | M1 suhbat navbati (yuqoridagi oqim), tasdiqlash (`/confirm`)                                                                                                                 | Structured output, holatga moslashuv                                         |
| `interpreter`                    | M3 tarjimon: `guess` (3 taxmin, 40 ehtiyoj lug'ati) → `confirm` (jumla + TTS + oila izohi) → `board` (piktogramma + tana xaritasi)                                           | LLM yo'q bo'lsa — alias/fuzzy zaxira; tasdiqlar dataset urug'i               |
| `exercises`                      | M2 nutq mashqlari: reja (8 ta, daraja + protokol), `next`/`submit`/`skip`, **CER ballash**, **cueing 0→3** (semantik → fonemik → model), LLM-hakam (partial), adaptiv daraja | `uz_text.normalize` (kirill→lotin, apostrof, sheva variantlari), 110 element |
| `safety`                         | Xavf klassifikatori (LLM + kalit so'zlar), xavfsiz skriptlar, eskalatsiya                                                                                                    | 6 kategoriya (A–F), `red_flags` + `audit_logs`                               |
| `notifications`                  | Telegram bot (havola kodi `/start <kod>`, poller), bayroq xabarlari, in-app ro'yxat                                                                                          | Shablonlar `templates_uz.py`                                                 |
| `clinician`, `reports`           | Bemorlar ro'yxati, **14 kunlik agregatlar** (aniqlik, mustaqillik, FSI, kayfiyat, rioya), sessiyalar, **haftalik hisobot** (LLM, markdown)                                   | Hisobot "vrach tekshiruvi uchun takliflar" — dori taklifi yo'q               |
| `caregiver`                      | Bugungi holat, **3 maslahat** (LLM), oxirgi tarjimon so'rovlari                                                                                                              | Telefon uchun kartochkalar                                                   |
| `state`                          | Fusion formulalari (deterministik)                                                                                                                                           | Hakamlarga "qora quti emas"                                                  |
| `tts`, `health`, `observability` | `/tts` (istalgan matn → kesh), `/health/providers` (zanjirlar, circuit), `provider_calls`                                                                                    | Kill-switch demo                                                             |
| `face` (frontend)                | MediaPipe: roll-to'g'rilash, IOD normalizatsiya, juft blendshape asimmetriyasi, **FSI**, takror hisoblagich, kalibrovka (10 s baza), 1 Hz agregatsiya → `face-metrics`       | Kadr serverga hech qachon ketmaydi                                           |

## 6. AI provayderlar va ishonchlilik (TZ §4.4, ADR-001)

- Har vazifa uchun `Protocol` interfeys + implementatsiyalar: `llm/{gemini,openai,mock}`, `stt/{worker,gemini,openai,mock}`, `tts/{gemini,worker,openai,browser,mock}`, `voice_emotion/{worker,mock}`.
- **`FallbackChain`**: tartib `.env`dan (`LLM_PROVIDERS=gemini,openai`, `STT_PROVIDERS=worker,gemini,openai`, `TTS_PROVIDERS=gemini,worker,browser`), har provayderga timeout, **circuit breaker** (3 ketma-ket xato → 60 s "ochiq"), har urinish `provider_calls`ga (latency, ok, error).
- `/status` sahifasi: worker online/offline, zanjirlar, circuit holati. **Kill-switch**: ngrok o'chsa STT worker circuit ochiladi → Gemini davom etadi.
- TTS keshi: `sha1(provider+text)` — statik promptlar/ishoralar/xavfsiz skriptlar oldindan generatsiya (`make pregen-tts`).

## 7. Multimodal "tushunish" — formulalar (TZ §5)

- **Yuz (brauzer)**: juft blendshape'lar (`mouthSmile`, `browOuterUp`, `eyeBlink`, …) uchun `asym = |L−R| / max(L,R,0.10)` (faqat faol juftlar ≥ 0.25); landmark o'lchovlar (og'iz burchagi 61/291, qosh 105/334, EAR 386/374 · 159/145) IOD (33↔263) ga normalangan, roll to'g'rilangan; `FSI = 1 − clamp(mean(asym…))`; `|yaw|,|pitch| > 25°` kadrlar o'lchovga kirmaydi; takror: `s ≥ 0.5` ≥ 0.5 s ushlab → `s ≤ 0.2` → +1; **baza** kalibrovka (progress = FSI − FSI_base, shaxsga nisbatan); ifoda taxmini faqat sog'lom tomondan.
- **Nutq**: CER = Levenshtein/len (normalizatsiyadan keyin), `correct ≥ 0.75 | partial 0.40–0.74 | incorrect`; STT ishonchi < 0.35 → "eshitolmadim"; bulut STT ishonchi 0.5.
- **Fusion**: `fatigue = 0.35·yuz + 0.25·kechikish + 0.20·xatolar + 0.20·vaqt`; `engagement` diqqat/kechikishdan; `mood` = og'irlangan (o'zi 0.5, ovoz 0.3, yuz 0.2); `distress` = ovoz (arousal↑, valence↓) ∨ grimace ∨ kalit so'z; `explain[]` odam o'qiydigan sabablar.

## 8. Ma'lumotlar modeli (26 jadval, TZ §4.5)

`users, clinics, patients, caregivers, consents, protocols, protocol_items, medications, medication_logs, sessions, messages, exercise_templates, exercise_attempts, face_metrics, hand_metrics, voice_metrics, patient_states, patient_levels, mood_entries, screenings, red_flags, interpretations, reports, notifications, provider_calls, audit_logs`. Hammasi `id uuid, created_at, updated_at`; JSON maydonlar Pydantic bilan validatsiya; indekslar `sessions(patient_id, started_at)`, `red_flags(patient_id, status)`, `face_metrics(session_id, ts)`.

## 9. Xavfsizlik, maxfiylik, tibbiy chegaralar

- JWT + bcrypt + RBAC; PII loglarga tushmaydi; `.env` repo'da yo'q.
- **Video serverga ketmaydi** (faqat raqamli metrikalar); audio saqlash siyosati `AUDIO_RETENTION_HOURS=24`.
- Prompt qoidalari (Ilova A) + **guardrail testlari**: "tashxis qo'yma", "dori o'zgartirma"; `high` xavfda LLM javobi **xavfsiz skript** bilan almashtiriladi; eskalatsiya odamga (oila + vrach), hamma bayroq audit'da, klinisist "ko'rdim/hal qilindi".
- Ochiq modellar (Kotib Apache-2.0, Navoiy Apache-2.0, MediaPipe Apache-2.0) on-prem ishlashi mumkin — ma'lumot chet elga chiqmaydi (bulut faqat zaxira/dialog).

## 10. Raqamlar

- 110 nutq mashqi (nomlash L1/L2, takrorlash, tugatish, avtomatik qatorlar, o'qish), 5 yuz mashqi, 12 kognitiv, 40 ehtiyoj + tana xaritasi, 4 protokol shabloni, 94 sheva/imlo varianti, 7 LLM prompt.
- 311 backend test, ~40 ekran/komponent; demo ma'lumoti: "Bobur aka" 14 kun (aniqlik 45→85 %, mustaqillik ↑, FSI 64→71 %, rioya 86 %, 1 bayroq), 2-bemor.

## 11. Bugun kesilganlar (halol)

PHQ-2/9 skrining, eslatmalar/kunlik 20:00 xulosa (cron), bemor PIN rejimi, SSE streaming, Web Push, rus tili, MedGemma hujjat tahlili, qo'l mashqlari, admin panel — TZ P1/P2, UI'da "tez orada".

## 12. Mentor savollariga qisqa javoblar

- **"STT afaziya nutqida ishlamaydi-ku?"** — Shuning uchun uch qatlam: kutilgan so'z bilan cheklangan tanish (`initial_prompt` + CER), 3 kandidatli tasdiqlash, piktogramma taxtasi. Har tasdiq — o'zbek afaziya nutqi datasetiga yozuv (keyin Kotib fine-tune).
- **"Yuz falajida ifoda noto'g'ri o'qiladi?"** — Ifoda taxmini faqat sog'lom tomondan; asosiy metrika ifoda emas — bemorning **o'z bazasiga** nisbatan simmetriya o'zgarishi.
- **"Nega LLM'ga ishonamiz?"** — LLM faqat matn yaratadi va structured JSON qaytaradi; xavf klassifikatori ikki qatlam (LLM + kalit so'zlar), `high` bo'lsa LLM javobi ishlatilmaydi; holat/ballash formulalari kodda, deterministik, testlangan.
- **"Internet/GPU uzilsa?"** — FallbackChain + circuit breaker; worker → Gemini → OpenAI; TTS keshi; `/status`da jonli ko'rsatiladi.
- **"Kechikish?"** — LLM 1.8 s, STT (Kotib, GPU) ~1 s, TTS 3–6 s; keshlangan promptlar 0 s; maqsad ≤ 5 s (Navoiy bilan 5.4 s o'lchandi).
- **"Ma'lumot xavfsizligi?"** — Video brauzerdan chiqmaydi; audio 24 soat; on-prem modellar; rozilik; RBAC; audit.
- **"Nega vrachni almashtirmaydi?"** — Protokolni vrach yozadi, AI bajartiradi/o'lchaydi/xabar beradi; hisobotdagi takliflar "vrach tekshiruvi uchun" belgisi bilan, dori taklifi yo'q.
- **"Masshtab?"** — Stateless FastAPI (gorizontal), Postgres, provayderlar plagin; worker'lar bir nechta bo'lishi mumkin (ro'yxat `.env`).
- **"Keyingi qadam?"** — O'zbek afaziya dataseti + Kotib fine-tune; Urganch tibbiyot instituti bilan klinik pilot (20 bemor, 8 hafta); Capacitor mobil, offline, rus tili.

## 13. Repo va buyruqlar

```
apps/web/src/{app,features,components,lib,i18n,workers}   apps/api/app/{core,api,db,ai,modules,seeds}
apps/api/app/ai/{providers,chains.py,audio.py,prompts,worker}   apps/ai_worker/app   packages/shared   docs/{TZ,DEMO,DEMO_SCOPE,AI_WORKER_TZ,adr}
make install · make dev · make demo · make test · make lint · make pregen-tts · make health
```
