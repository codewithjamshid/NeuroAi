from datetime import datetime

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.ai.worker.client import WorkerClient


@pytest.mark.parametrize("path", ["/health", "/api/v1/health"])
async def test_health_ok(client: AsyncClient, path: str) -> None:
    resp = await client.get(path)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "neuroai-api"
    assert body["version"] == "0.1.0"
    assert body["env"] == "test"
    assert datetime.fromisoformat(body["time"]).tzinfo is not None


async def test_request_id_echoed_and_generated(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health", headers={"X-Request-ID": "req-abc-123"})
    assert resp.headers["x-request-id"] == "req-abc-123"

    resp = await client.get("/api/v1/health")
    assert len(resp.headers["x-request-id"]) == 36  # uuid4


async def test_providers_mock_worker_online(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/providers")
    assert resp.status_code == 200
    body = resp.json()
    worker = body["worker"]
    assert worker["mode"] == "mock"
    assert worker["url"] == "mock"
    assert worker["status"] == "online"
    assert worker["latency_ms"] >= 0
    assert set(worker["models"].values()) == {"mock"}
    for key in ("llm", "stt", "tts", "voice_emotion"):
        assert body[key] == []


async def test_providers_http_worker_offline_and_masked(app: FastAPI, client: AsyncClient) -> None:
    def refuse(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    app.state.worker_client = WorkerClient(
        base_url="https://abc-123.ngrok-free.app",
        key="k",
        timeout_s=1,
        transport=httpx.MockTransport(refuse),
    )
    resp = await client.get("/api/v1/health/providers")
    assert resp.status_code == 200
    worker = resp.json()["worker"]
    assert worker["mode"] == "http"
    assert worker["status"] == "offline"
    assert worker["url"] == "https://***.ngrok-free.app"
    await app.state.worker_client.aclose()


async def test_404_error_envelope(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    assert resp.json() == {"error": {"code": "http_404", "message": "Not Found"}}


async def test_validation_error_envelope(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/_test/{n}")
    async def _echo(n: int) -> dict[str, int]:
        return {"n": n}

    resp = await client.get("/_test/abc")
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["path", "n"]


async def test_500_envelope_keeps_request_id_and_cors(app: FastAPI) -> None:
    @app.get("/_boom")
    async def _boom() -> None:
        raise RuntimeError("boom")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    headers = {"X-Request-ID": "rid-500", "Origin": "http://localhost:3000"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/_boom", headers=headers)
    assert resp.status_code == 500
    error = resp.json()["error"]
    assert error == {"code": "internal_error", "message": "Ichki xatolik yuz berdi"}
    assert resp.headers["x-request-id"] == "rid-500"
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_docs_available(client: AsyncClient) -> None:
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/v1/health" in paths and "/api/v1/health/providers" in paths
    assert "/health" not in paths  # root alias is hidden from the schema
