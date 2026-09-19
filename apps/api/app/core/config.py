"""Settings — the only place that reads environment / `.env` (CLAUDE.md, ADR-005).

Precedence: process env > apps/api/.env > <repo root>/.env > defaults. Defaults boot the app
with no `.env` at all (sqlite + mock worker).
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]  # apps/api (or /app inside docker)
REPO_ROOT = API_DIR.parents[1] if len(API_DIR.parents) > 1 else API_DIR
ENV_FILES = tuple(dict.fromkeys((REPO_ROOT / ".env", API_DIR / ".env")))

# Comma-separated env values ("a,b,c") → list[str]; NoDecode stops the JSON parse attempt.
CsvList = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Umumiy ---
    app_env: str = "dev"
    demo_mode: bool = True
    jwt_secret: str = "change-me"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    media_dir: Path = Path("./media")
    audio_retention_hours: int = 24
    default_locale: str = "uz-Latn"
    emergency_number: str = "103"
    unified_emergency: str = "112"
    mental_health_hotline: str = ""

    # --- AI worker (ofis GPU, ngrok); "mock" → MockWorkerClient ---
    ai_worker_url: str = "mock"
    ai_worker_key: str = ""
    ai_worker_timeout_s: float = 4.0

    # --- Bulut provayderlar ---
    gemini_api_key: str = ""
    gemini_model_fast: str = "gemini-2.5-flash"
    gemini_model_pro: str = "gemini-2.5-pro"
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_stt_model: str = "gpt-4o-transcribe"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"

    # --- Provayder zanjirlari (tartib = ustuvorlik) ---
    llm_providers: CsvList = ["gemini", "openai"]
    stt_providers: CsvList = ["worker", "gemini", "openai"]
    tts_providers: CsvList = ["worker", "openai", "browser"]
    voice_emotion_providers: CsvList = ["worker"]
    llm_temperature: float = 0.4
    tts_speed: float = 0.85

    # --- Xabarnomalar ---
    telegram_bot_token: str = ""
    daily_summary_time: str = "20:00"

    # --- Dev / infra ---
    api_port: int = 8000
    web_port: int = 3000
    # Empty → derived from web_port (ADR-005), so changing WEB_PORT alone keeps the browser working.
    cors_origins: CsvList = []
    log_level: str = "INFO"

    @field_validator(
        "llm_providers",
        "stt_providers",
        "tts_providers",
        "voice_emotion_providers",
        "cors_origins",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def _default_cors_from_web_port(self) -> "Settings":
        if not self.cors_origins:
            self.cors_origins = [
                f"http://localhost:{self.web_port}",
                f"http://127.0.0.1:{self.web_port}",
            ]
        return self

    @property
    def worker_is_mock(self) -> bool:
        return self.ai_worker_url.strip().lower() == "mock"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
