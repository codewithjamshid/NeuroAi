# apps/ai_worker — NeuroAI AI worker (GPU servis)

TZ §4.7: `POST /stt`, `POST /tts`, `POST /voice-emotion`, `POST /medllm/summarize`, `GET /health`.
Barcha model endpointlari `X-Worker-Key` sarlavhasini talab qiladi; `/health` ochiq.

| Qayerda                 | Nima                                                                                                                                                                                                  |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Laptop**              | Faqat skelet: ML kutubxonalari yo'q, `/health` → hamma model `disabled`, model endpointlari → `503 model_not_loaded`. `api` esa `AI_WORKER_URL=mock` bilan ishlaydi.                                  |
| **Ofis GPU kompyuteri** | Haqiqiy implementatsiya — `docs/AI_WORKER_TZ.md` (Python 3.11, CUDA). `app/{stt,tts,emotion,medllm}.py` ichida faqat `load()` / task funksiyasi to'ldiriladi; og'ir importlar `load()` ichida qoladi. |

## Ishga tushirish

```bash
cd apps/ai_worker
uv sync                                   # laptop: faqat fastapi/uvicorn/pydantic
uv run uvicorn app.main:app --port 8001   # yoki: make worker (root)
curl localhost:8001/health
curl -X POST localhost:8001/stt -H "X-Worker-Key: $WORKER_KEY" -F audio=@sample.wav   # laptop: 503
```

Sozlamalar (`app/config.py`, pydantic-settings; ustuvorlik: env > `apps/ai_worker/.env` > root `.env`):
`WORKER_KEY`, `WORKER_PORT`, `MODELS_ENABLED=stt,tts,voice_emotion[,medllm]`, `STT_MODEL_PATH`,
`STT_COMPUTE_TYPE`, `TTS_MODEL_PATH`, `EMOTION_MODEL`, `AVD_MODEL`, `MEDLLM_MODEL`, `LOG_LEVEL`.
Namuna: `.env.example`. Laptopda `MODELS_ENABLED` bo'sh qoldiriladi; TZ qiymati
(`stt,tts,voice_emotion`) qolib ketsa ham zarar yo'q — kutubxonalar yo'qligi uchun ular `disabled` bo'ladi.

Startup: `MODELS_ENABLED`dagi har model uchun `load()` + `warmup()`; servis har holda ko'tariladi.
`/health` holatlari: `loaded`; `disabled` — ro'yxatda yo'q **yoki** kutubxona/model shu mashinada
mavjud emas (`load()` → `ModelUnavailable`, ogohlantirish log'da); `error` — kutubxona bor, lekin
yuklash haqiqatan xato berdi (model papkasi yo'q, CUDA xatosi — traceback log'da).

## Ofis kompyuterida (qisqa)

```bash
pip install -r requirements.txt            # + izohdagi GPU blokini oching
bash scripts/prepare_models.sh             # nvidia-smi bo'lmasa to'xtaydi
MODELS_ENABLED=stt,tts,voice_emotion uvicorn app.main:app --host 0.0.0.0 --port 8001
ngrok http 8001 --domain=<static>.ngrok-free.app   # TZ §4.1; api: AI_WORKER_URL=https://<static>.ngrok-free.app
```

`api` klienti har so'rovga `X-Worker-Key` va `ngrok-skip-browser-warning: 1` qo'shadi (TZ §4.4).

## Tekshiruv

```bash
uv run ruff check . && uv run black --check . && uv run pytest -q
```

Xato formati: `{"error": {"code": "unauthorized" | "model_not_loaded" | "validation_error", "message": "..."}}`.
