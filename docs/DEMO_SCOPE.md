# DEMO_SCOPE — bir kunlik siqilgan reja (2026-09-19, demo'gacha < 4 soat)

TZ 4 kunga mo'ljallangan; demo bugun. Shu hujjat TZ §9.4 ticket'larini **qisqartirilgan** holda belgilaydi.
Manba haqiqat: `docs/TZ.md` (API shakllari §4.6, sxemalar Ilova B, promptlar Ilova A). Bu yerda faqat **kesish** va **qarorlar**.

## Kesiladi (halol "tez orada" bilan)

| Nima                                                                                        | Sabab                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T-07/T-08/T-10 yuz (MediaPipe, FSI, fusion)                                                 | Faqat **stretch**: alohida frontend agent `/p/exercise/face` (worker + FSI + reps); backend faqat `POST /sessions/{id}/face-metrics` saqlaydi. `PatientState` — soddalashtirilgan (nutq + kayfiyat + kalit so'z) |
| T-16 PHQ-2/9                                                                                | Kayfiyat 1–5 qoladi, PHQ yo'q                                                                                                                                                                                    |
| T-18 barqarorlik, Playwright                                                                | Faqat asosiy xato holatlari UI (mikrofon yo'q, provayder yo'q)                                                                                                                                                   |
| T-19 P2 (MedGemma, qo'l, admin, ru, push, WS)                                               | Yo'q                                                                                                                                                                                                             |
| Bemor PIN rejimi, SSE streaming, audio retention cron, 20:00 kunlik xulosa cron, eslatmalar | Yo'q; Telegram faqat bayroq xabari + havola kodi                                                                                                                                                                 |
| Parvarishchi telefoni                                                                       | Xuddi shu laptopda 2-tab (`/c/say` polling 2 s) — cloudflared ixtiyoriy                                                                                                                                          |

## Qoladi (demo ssenariysi §11.2 bo'yicha)

1. Login (demo tugmalari) → rol bo'yicha `/p` `/c` `/d`.
2. Klinisist: protokol shablonidan yaratadi → bemor `/p`da "Bugungi reja".
3. `/p/talk`: mikrofon → STT (worker→Gemini→OpenAI) → LLM (Gemini structured, `companion.md`) → TTS (worker→OpenAI→brauzer) → ovoz + matn + holat paneli (soddalashtirilgan) + kandidat kartalar.
4. `/p/say` + `/p/board` + `/c/say`: tarjimon (3 karta → tasdiq → ovoz + oila izohi), tarix.
5. `/p/exercise`: nomlash/takrorlash, CER ballash, cueing 0→3, adaptiv daraja, TTS.
6. (stretch) `/p/exercise/face`: kamera, FSI jonli, tabassum takrorlari.
7. Xavfsizlik: LLM `risk` + kalit so'zlar → xavfsiz skript + `red_flags` + Telegram → `/d`da bayroq → "ko'rdim".
8. `/d`: bemorlar jadvali; `/d/patients/[id]`: 4 grafik (14 kun, demo data), sessiyalar, bayroqlar, protokol, hisobot (Gemini Pro).
9. `/c`: bugungi holat, maslahatlar (LLM), oxirgi tarjimon so'rovlari, Telegram ulash kodi.
10. `/status`: provayderlar; worker o'chsa bulut rejimi (kill-switch).
11. `make demo` — "Bobur aka" 14 kunlik ma'lumot + 2-bemor.

## Qat'iy qarorlar

- Rollar: `patient | caregiver | clinician | admin`; demo akkauntlar: `logoped@demo.uz`, `qizi@demo.uz`, **`bemor@demo.uz`** (bemor akkaunti — PIN o'rniga), parol `demo1234`.
- JWT (access 24h, refresh 30d), `Authorization: Bearer`; RBAC `require_roles(...)` dependency; frontend token `localStorage` (`neuroai.auth`), `apiFetch` avtomatik qo'shadi, 401 → `/login`.
- Audio: brauzer `MediaRecorder` (webm/opus) → API `ffmpeg` (static-ffmpeg paketi yoki tizim) → 16 kHz mono wav. Energiya-VAD: 1.2 s jimlik → to'xtash, maks 15 s.
- Provayderlar (`app/ai/providers/<task>/`): `Protocol` + `gemini.py` / `openai.py` / `worker.py` / `mock.py`; `FallbackChain` (timeout, 3 xato → 60 s ochiq, `provider_calls` yozuvi callback orqali). LLM structured output: Gemini `response_schema` (Pydantic → JSON schema), OpenAI `response_format` json_schema. Bulut STT ishonchi = 0.5 (TZ §5.2). TTS kesh `media/tts/<sha1>.wav`.
- DB: TZ §4.5 dagi **barcha** jadvallar bitta boshlang'ich migratsiyada (`clinics`, `hand_metrics`, `screenings` ham — bo'sh); JSON ustunlar `JSON().with_variant(JSONB, "postgresql")`.
- Xato konverti `{error:{code,message}}`; sahifalash `?limit&offset`.
- Frontend: `features/<name>/{api,hooks,components}`, Zustand `session`/`state`/`audio`/`auth`, TanStack Query, Recharts (`/d`), barcha matnlar `i18n/uz.json`.

## Fayl egaligi (parallel agentlar to'qnashmasligi uchun)

| Egasi           | Yo'llar                                                                                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| backend-core    | `apps/api/app/modules/{auth,users,patients,protocols,sessions}/`, `app/db/registry.py`, `alembic/versions/`, `app/api/deps.py`, `scripts/seed.py`, `tests/test_auth*.py`, `tests/test_models*.py`                                           |
| providers       | `apps/api/app/ai/providers/**`, `app/ai/chains.py`, `app/ai/audio.py`, `app/modules/health/`, `tests/test_providers*.py`                                                                                                                    |
| content         | `apps/api/app/seeds/*.json`, `app/ai/prompts/*.md`, `app/core/uz_text.py`, `app/modules/exercises/scoring.py`, `app/modules/safety/keywords_uz.py`, `tests/test_scoring*.py`, `tests/test_prompts_guardrails.py`, `tests/test_keywords*.py` |
| web             | `apps/web/**`                                                                                                                                                                                                                               |
| Keyingi to'lqin | `modules/{companion,interpreter,exercises(router/service),safety,notifications,clinician,caregiver,reports}`, `scripts/demo_data.py`                                                                                                        |

Umumiy fayllar: `app/api/v1/router.py` **avto-discovery** qiladi (`app.modules.<name>.router:router`) — tahrirlanmaydi; `app/main.py` tahrirlanmaydi (`/media/tts` static allaqachon mount qilingan); `app/db/registry.py` — backend-core to'ldiradi; `pyproject.toml`/`uv.lock`/`package.json` — bog'liqliklar orkestrator tomonidan oldindan qo'shilgan (`bcrypt pyjwt google-genai openai static-ffmpeg rapidfuzz`; web: `recharts react-markdown @mediapipe/tasks-vision`), **`uv add`/`pnpm add` qilinmaydi**; kerak bo'lsa hisobotda so'raladi.

## API kontrakt — TZ §4.6 ga qo'shimcha aniq shakllar (frontend va backend shu bo'yicha)

- **Auth:** `POST /auth/login {email,password}` → `{access, refresh, user:{id, role, full_name, patient_id?}}`; `POST /auth/refresh {refresh}` → `{access, refresh}`; `GET /me` → `{id, role, full_name, email, locale, patient_id?}` (`patient_id` — bemor akkaunti yoki parvarishchining asosiy bemori).
- **Patients:** `GET /patients` → `[{id, full_name, birth_year, sex, stroke_date, affected_side, aphasia_type, dialect, interests, family_members, habits, clinician_id}]` (klinisist: o'ziniki; parvarishchi: bog'langanlari); `POST /patients` (karta + `consent:{scopes}`), `GET/PATCH /patients/{id}`.
- **Today:** `GET /patients/{id}/today` → `{date, items:[{id, kind:"exercise"|"medication"|"checkin", title, category?, level?, duration_min?, time?, done, protocol_item_id?, medication_id?}], mood_self?}`.
- **Protokol:** `GET /protocol-templates` → `[{key, title, description, items:[{kind, category, level, frequency, duration_min}]}]`; `POST /patients/{id}/protocol {template_key?, title?, items?}` → `{id, title, status, start_date, items:[{id, kind, category, level, frequency, duration_min, params}]}`; `GET /patients/{id}/protocol` → faol protokol yoki `null`; `PATCH /protocols/{id}`, `POST /protocols/{id}/items`, `PATCH/DELETE /protocol-items/{id}`; `GET/POST /patients/{id}/medications`, `POST /medications/{id}/log {status}`.
- **Sessiya:** `POST /sessions {patient_id, mode}` → `{id, patient_id, mode, started_at}`; `POST /sessions/{id}/end` → `{summary:{caregiver_text, clinician_text, attention_needed}}`; `GET /sessions/{id}/transcript` → `{session:{...}, messages:[{id, role, modality, text, audio_url?, stt_confidence?, created_at, llm_meta?}]}`.
- **Xabar:** `POST /sessions/{id}/messages` multipart (`audio` | `text` | `pictogram_key`, ixtiyoriy `face_batch` JSON) → TZ §4.6 JSON (`patient_message`, `ai_message:{text, tts_url|null, tts_provider}`, `needs_confirmation`, `candidates`, `state`, `risk`, `suggested_action`); `POST /sessions/{id}/confirm {candidate_key}` → xuddi shu shakl.
- **Holat/yuz:** `GET /sessions/{id}/state` → `PatientState` (Ilova B); `POST /sessions/{id}/face-metrics [..]` → `{stored}`.
- **Mashq:** `GET /sessions/{id}/exercises/next` → `{attempt_id, template:{id, category, subtype, level, prompt_text, prompt_tts_url?, stimulus, cues}, cue_level, progress:{index, total}}` yoki `{done:true, summary:{accuracy, independence, attempts}}`; `POST /exercise-attempts/{id}/submit` multipart `audio`|`text`|`face_summary` → `{score, result, recognized_text, feedback_text, tts_url?, next_action, next_cue?:{level, text, tts_url?}}`; `POST /exercise-attempts/{id}/skip` → `{ok}`.
- **Tarjimon:** `POST /interpreter/guess` multipart `audio`|`text` + `patient_id` + `session_id?` → `{interpretation_id, raw_transcript, confidence, candidates:[{key,label,emoji,p}], board_suggested}`; `POST /interpreter/confirm {interpretation_id, candidate_key?, custom_text?}` → `{spoken_text, tts_url?, family_note, follow_up}`; `GET /interpreter/board?patient_id` → `{items:[{key,label,emoji,group}], body_map:[{key,label}]}`; `GET /patients/{id}/interpretations?limit` → `[{id, raw_transcript, chosen, spoken_text, family_note, confirmed_by, created_at}]`.
- **Kayfiyat/bayroq:** `POST /patients/{id}/mood {self_score}`; `GET /patients/{id}/mood/trend?days=14` → `[{date, self_score?, valence?}]`; `GET /patients/{id}/red-flags?status` → `[{id, category, severity, evidence, detector, status, session_id?, created_at}]`; `PATCH /red-flags/{id} {status, note?}`.
- **Klinisist:** `GET /clinician/patients` → `[{id, full_name, age, aphasia_type, open_flags, last_activity, adherence_week}]`; `GET /patients/{id}/dashboard` → `{days:[{date, speech_accuracy?, independence?, avg_cue_level?, fsi?, mood_self?, valence?, adherence_exercise?, adherence_medication?}], flags:[...], adherence_week:{exercise, medication}, sessions_count, fsi_base?}`; `GET /clinician/patients/{id}/sessions?limit` → `[{id, mode, started_at, ended_at, summary, accuracy?, attempts?}]`.
- **Hisobot:** `POST /patients/{id}/reports/generate?period=7d` → `{id, content_md, metrics, generated_by, period_start, period_end}`; `GET /patients/{id}/reports` → `[...]`.
- **Parvarishchi:** `GET /caregiver/patients/{id}/today` → `{state?, mood_self?, exercises_done, exercises_planned, last_interpretations:[...], flags_open, tips_cached?}`; `GET /caregiver/patients/{id}/tips` → `{tips:[3 ta]}`; `POST /notifications/telegram/link` → `{code, bot_username?}`; `GET /notifications/telegram/status` → `{linked}`.
- **Media:** `GET /media/tts/{file}` va `GET /api/v1/media/tts/{file}` (statik, tayyor).
