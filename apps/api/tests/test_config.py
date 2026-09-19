from pathlib import Path

from app.core.config import API_DIR, REPO_ROOT, Settings


def _clear_settings_env(monkeypatch) -> None:
    # `make test` exports the whole root .env (ADR-005); defaults must be asserted on a clean env.
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
        monkeypatch.delenv(name, raising=False)


def test_defaults_boot_without_env_file(monkeypatch) -> None:
    _clear_settings_env(monkeypatch)
    s = Settings(_env_file=None)
    assert s.database_url == "sqlite+aiosqlite:///./dev.db" and s.is_sqlite
    assert s.ai_worker_url == "mock" and s.worker_is_mock
    assert s.api_port == 8000
    assert s.llm_providers == ["gemini", "openai"]
    assert s.cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_csv_lists_and_case_insensitive_env(monkeypatch) -> None:
    monkeypatch.setenv("stt_providers", " worker, gemini ,,openai ")
    monkeypatch.setenv("CORS_ORIGINS", "http://a:3000")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    s = Settings(_env_file=None)
    assert s.stt_providers == ["worker", "gemini", "openai"]
    assert s.cors_origins == ["http://a:3000"]
    assert s.log_level == "DEBUG"


def test_cors_origins_follow_web_port_when_unset(monkeypatch) -> None:
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("WEB_PORT", "3020")
    assert Settings(_env_file=None).cors_origins == [
        "http://localhost:3020",
        "http://127.0.0.1:3020",
    ]
    monkeypatch.setenv("CORS_ORIGINS", "https://demo.example")
    assert Settings(_env_file=None).cors_origins == ["https://demo.example"]


def test_unknown_env_keys_are_ignored(monkeypatch) -> None:
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("WORKER_KEY", "x")  # ai_worker's own variable from the shared .env
    assert Settings(_env_file=None).ai_worker_key == ""


def test_paths_point_at_repo_and_api_dir() -> None:
    assert API_DIR.name == "api" and API_DIR.parent.name == "apps"
    assert (REPO_ROOT / ".env.example").exists()
    assert Path(API_DIR / "pyproject.toml").exists()
