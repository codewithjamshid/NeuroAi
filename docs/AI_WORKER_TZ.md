# AI worker — ofis GPU kompyuteri uchun topshiriq (qisqa)

> **Holat:** T-01 stub. To'liq hujjat ofis kompyuterida (Cursor) T-05 da to'ldiriladi.
> Laptopda **hech qanday model o'rnatilmaydi** — bu yerdagi hamma narsa ofis GPU mashinasi uchun.
> Manba: `docs/TZ.md` §4.1, §4.3, §4.7, Ilova D/E; skelet: `apps/ai_worker/`.

## Nima qilinadi

`apps/ai_worker` — FastAPI servis (port **8001**), `X-Worker-Key` bilan himoyalangan, ngrok static domain orqali
laptopdagi `apps/api` ga `AI_WORKER_URL` sifatida beriladi. Modellar (`MODELS_ENABLED=stt,tts,voice_emotion[,medllm]`):

| Endpoint                 | Model                                                                                | Izoh                                              |
| ------------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------- |
| `POST /stt`              | `Kotib/uzbek_stt_v1` → CTranslate2 float16 (`faster-whisper`)                        | `scripts/prepare_models.sh` konvertatsiya         |
| `POST /tts`              | `aisha-org/navoiy-tts` (CosyVoice2-0.5B), tezlik 0.85                                | 2 soat limit; bo'lmasa OpenAI TTS asosiy (TZ §12) |
| `POST /voice-emotion`    | `emotion2vec/emotion2vec_plus_base` (label) + `audeering/wav2vec2-…-msp-dim` (A/V/D) | P1                                                |
| `POST /medllm/summarize` | `google/medgemma-1.5-4b-it` (4-bit)                                                  | P2                                                |
| `GET /health`            | —                                                                                    | ochiq, yuklangan modellar + GPU                   |

Kod joyi: `app/{stt,tts,emotion,medllm}.py` — har birida `load()` (og'ir importlar **faqat** shu ichida) va vazifa funksiyasi;
`TODO(office)` belgilari aynan shu joylar. `app/main.py`, auth, xato konverti tayyor — o'zgartirish shart emas.

## HTTP kontrakt (laptopdagi `apps/api/app/ai/worker/client.py` shunday chaqiradi)

Har so'rovda sarlavhalar: `X-Worker-Key: <WORKER_KEY>` va `ngrok-skip-browser-warning: 1`. Timeout: 4 s (`AI_WORKER_TIMEOUT_S`).

- `POST /stt?lang=uz&initial_prompt=<kutilgan so'zlar>` — multipart, maydon `audio` (`audio.wav`, 16 kHz mono)
  → `{"text": str, "confidence": 0..1, "segments": [{"start","end","text","avg_logprob"}], "latency_ms": int}`
  `confidence = sigmoid((avg_logprob + 1.0) * 4)` (TZ §5.2).
- `POST /tts` — JSON `{"text": str, "speed": 0.85, "style": "neutral"}` → `audio/wav` baytlar (16 kHz mono).
- `POST /voice-emotion` — multipart `audio` → `{"label": str, "scores": {…}, "arousal", "valence", "dominance" (0..1), "latency_ms"}`.
- `GET /health` → `{"models": {"stt": "loaded|disabled|error", "tts": …, "voice_emotion": …, "medllm": …}, "gpu": {"name", "mem_used_mb"} | null, "version"}`.
- Xatolar: `{"error": {"code", "message"}}`; kalit noto'g'ri → 401 `unauthorized`; model yuklanmagan → 503 `model_not_loaded`.

## Ishga tushirish (ofis)

```bash
cd apps/ai_worker && cp .env.example .env      # WORKER_KEY = laptopdagi AI_WORKER_KEY bilan bir xil
pip install -r requirements.txt                # izohdagi GPU bloklarini oching (torch, faster-whisper, funasr, …)
bash scripts/prepare_models.sh                 # Kotib → CT2, Navoiy, emotion modellari
uvicorn app.main:app --host 0.0.0.0 --port 8001
ngrok http 8001 --domain=<static>.ngrok-free.app
```

Laptopda `.env`: `AI_WORKER_URL=https://<static>.ngrok-free.app`, `AI_WORKER_KEY=<WORKER_KEY>`; tekshiruv: `make health`
va `GET /api/v1/health/providers` → `worker.status = online`.

## DoD (T-05, TZ §9.4)

Laptopdan `curl` bilan 3 endpoint javob beradi; STT latency ≤ 1.5 s (10 s audio); `AI_WORKER_URL=mock` bilan API to'liq ishlaydi.
