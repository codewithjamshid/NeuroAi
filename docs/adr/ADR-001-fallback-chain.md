# ADR-001 — AI provayderlar uchun `FallbackChain` + circuit breaker

**Sana:** 2026-09-19 · **Holat:** qabul qilingan (TZ §4.3–4.4 dan yozib olindi)

## Kontekst

Asosiy STT/TTS/emotion modellar ofis GPU kompyuterida (`ai_worker`, ngrok orqali) ishlaydi.
Ngrok/GPU uzilishi ehtimoli yuqori; demo to'xtab qolmasligi kerak.

## Qaror

Har AI vazifa (`llm`, `stt`, `tts`, `voice_emotion`) uchun `Protocol` interfeys va bir nechta
implementatsiya (`worker`, `gemini`, `openai`, `browser`, `mock`). Ular `FallbackChain`
orqali chaqiriladi: tartib `.env` (`STT_PROVIDERS=worker,gemini,openai`), har provayderga
timeout, 3 ketma-ket xato → 60 s "ochiq" (circuit breaker), har chaqiruv `provider_calls`ga.
`AI_WORKER_URL=mock` bo'lsa `worker_mock` ishlaydi (laptop mustaqil).

## Oqibatlar

- Router hech qachon provayderni to'g'ridan-to'g'ri chaqirmaydi (faqat `service` → `chain`).
- `/health/providers` har provayder holatini ko'rsatadi; demo'da kill-switch ko'rsatiladi.
- T-04 da amalga oshiriladi; T-01 faqat worker klienti + mock skeletini beradi.
