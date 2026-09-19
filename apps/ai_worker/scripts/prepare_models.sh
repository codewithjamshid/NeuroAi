#!/usr/bin/env bash
# NeuroAI AI worker — modellarni tayyorlash. FAQAT ofis CUDA GPU kompyuterida (docs/AI_WORKER_TZ.md).
# Laptopda hech qanday model o'rnatilmaydi (CLAUDE.md) — skript nvidia-smi bo'lmasa to'xtaydi.
#
# Talablar (ofis, Python 3.11 venv/conda): requirements.txt dagi izohli bloklar + `huggingface_hub[cli]`.
# Natija: ./models/kotib-ct2 (STT), ./models/navoiy-tts (TTS); emotion/MedGemma HF keshida.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "prepare_models.sh: nvidia-smi topilmadi — bu CUDA GPU kompyuteri emas." >&2
  echo "Laptopda modellar o'rnatilmaydi. Skriptni ofis GPU kompyuterida ishga tushiring (docs/AI_WORKER_TZ.md)." >&2
  exit 1
fi
echo "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"

MODELS_DIR="${MODELS_DIR:-./models}"
mkdir -p "$MODELS_DIR"

# 1) STT — Kotib/uzbek_stt_v1 (Whisper-medium) → CTranslate2 float16 (TZ §4.7)
if [ -f "$MODELS_DIR/kotib-ct2/model.bin" ]; then
  echo "STT: $MODELS_DIR/kotib-ct2 mavjud — o'tkazib yuborildi"
else
  ct2-transformers-converter --model Kotib/uzbek_stt_v1 --output_dir "$MODELS_DIR/kotib-ct2" --quantization float16
fi

# 2) TTS — Navoiy (aisha-org/navoiy-tts, CosyVoice2-0.5B). Aniq repo/skript: docs/AI_WORKER_TZ.md
# huggingface-cli download aisha-org/navoiy-tts --local-dir "$MODELS_DIR/navoiy-tts"

# 3) Ovoz hissiyoti — HF keshiga oldindan yuklash (birinchi so'rovda ham avtomatik yuklanadi)
# huggingface-cli download emotion2vec/emotion2vec_plus_base
# huggingface-cli download audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim

# 4) MedLLM (P2, gated → avval `huggingface-cli login`)
# huggingface-cli download google/medgemma-1.5-4b-it

echo "Tayyor. Ishga tushirish: MODELS_ENABLED=stt,tts,voice_emotion uvicorn app.main:app --port 8001"
