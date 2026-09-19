"""Worker settings (pydantic-settings). Env names = TZ Ilova D, "ai_worker" block.

Precedence: process env > apps/ai_worker/.env > <repo root>/.env (ADR-005).
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent.parent  # apps/ai_worker
REPO_ROOT = APP_DIR.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # later files override earlier ones
        env_file=(REPO_ROOT / ".env", APP_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    worker_key: str = ""
    worker_port: int = 8001
    log_level: str = "INFO"

    # comma list: stt,tts,voice_emotion[,medllm]; empty on the laptop
    models_enabled: str = ""

    stt_model_path: str = "./models/kotib-ct2"
    stt_compute_type: str = "float16"
    tts_model_path: str = "./models/navoiy-tts"
    emotion_model: str = "emotion2vec/emotion2vec_plus_base"
    avd_model: str = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
    medllm_model: str = "google/medgemma-1.5-4b-it"

    @property
    def enabled_models(self) -> list[str]:
        return [m.strip() for m in self.models_enabled.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
