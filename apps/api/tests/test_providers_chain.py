"""FallbackChain with fakes (TZ §4.4): order, timeout, circuit breaker, records, sinks."""

import asyncio
from collections.abc import Iterator

import pytest

from app.ai import chains as chains_mod
from app.ai.chains import FallbackChain, recent_calls, set_record_sink
from app.ai.providers.base import ProviderCallRecord, ProviderUnavailable


class Fake:
    def __init__(
        self, name: str, *, fail: bool = False, delay: float = 0.0, configured: bool = True
    ) -> None:
        self.name = name
        self.fail = fail
        self.delay = delay
        self.configured = configured
        self.calls = 0

    async def run(self, x: str) -> str:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise RuntimeError("boom")
        return f"{self.name}:{x}"


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    chains_mod.reset_chains()
    set_record_sink(None)
    yield
    set_record_sink(None)
    chains_mod.reset_chains()


async def test_order_and_fallback_on_exception() -> None:
    a, b, c = Fake("a", fail=True), Fake("b"), Fake("c")
    chain: FallbackChain[Fake] = FallbackChain([a, b, c], timeout_s=1, task="t")
    assert await chain.call("run", "x") == "b:x"
    assert (a.calls, b.calls, c.calls) == (1, 1, 0)
    records = recent_calls()
    assert [(r.provider, r.ok, r.fallback_index) for r in records] == [
        ("b", True, 1),
        ("a", False, 0),
    ]
    assert records[1].error is not None and records[1].error.startswith("RuntimeError")
    assert records[0].task == "t" and records[0].latency_ms >= 0


async def test_timeout_moves_to_next_provider() -> None:
    slow, fast = Fake("slow", delay=0.3), Fake("fast")
    chain: FallbackChain[Fake] = FallbackChain([slow, fast], timeout_s=0.05, task="t")
    assert await chain.call("run", "x") == "fast:x"
    failed = next(r for r in recent_calls() if r.provider == "slow")
    assert failed.ok is False and failed.error is not None and "ProviderTimeout" in failed.error
    assert chain.status()[0]["last_error"] == failed.error


async def test_circuit_opens_after_threshold_and_skips() -> None:
    a, b = Fake("a", fail=True), Fake("b")
    chain: FallbackChain[Fake] = FallbackChain(
        [a, b], timeout_s=1, task="t", circuit_fail_threshold=3
    )
    for _ in range(2):
        await chain.call("run", "x")
    assert chain.status()[0]["circuit"] == "closed"
    await chain.call("run", "x")
    assert a.calls == 3
    assert chain.status()[0]["circuit"] == "open"
    assert chain.status()[0]["status"] == "offline"
    await chain.call("run", "x")
    assert a.calls == 3  # skipped while open
    assert b.calls == 4


async def test_circuit_resets_after_reset_s(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = {"t": 1000.0}
    monkeypatch.setattr(chains_mod, "_now", lambda: clock["t"])
    a, b = Fake("a", fail=True), Fake("b")
    chain: FallbackChain[Fake] = FallbackChain(
        [a, b], timeout_s=1, task="t", circuit_fail_threshold=3, circuit_reset_s=60
    )
    for _ in range(3):
        await chain.call("run", "x")
    assert chain.status()[0]["circuit"] == "open"
    clock["t"] += 59
    await chain.call("run", "x")
    assert a.calls == 3  # still open
    clock["t"] += 2
    await chain.call("run", "x")
    assert a.calls == 4  # half-open try, failed → re-opened
    assert chain.status()[0]["circuit"] == "open"
    a.fail = False
    clock["t"] += 61
    assert await chain.call("run", "x") == "a:x"
    status = chain.status()[0]
    assert status["circuit"] == "closed" and status["status"] == "online"
    assert status["last_ok"] is True and status["last_error"] is None


async def test_all_fail_raises_provider_unavailable() -> None:
    chain: FallbackChain[Fake] = FallbackChain(
        [Fake("a", fail=True), Fake("b", fail=True)], timeout_s=1, task="stt"
    )
    with pytest.raises(ProviderUnavailable) as exc:
        await chain.call("run", "x")
    assert exc.value.task == "stt"
    assert [r.ok for r in recent_calls()] == [False, False]


async def test_empty_chain_raises_provider_unavailable() -> None:
    chain: FallbackChain[Fake] = FallbackChain([], timeout_s=1, task="voice_emotion")
    with pytest.raises(ProviderUnavailable):
        await chain.call("run", "x")


async def test_unconfigured_provider_skipped() -> None:
    a, b = Fake("a", configured=False), Fake("b")
    chain: FallbackChain[Fake] = FallbackChain([a, b], timeout_s=1)
    assert await chain.call("run", "x") == "b:x"
    assert a.calls == 0
    assert chain.status()[0] == {
        "name": "a",
        "configured": False,
        "circuit": "closed",
        "status": "unknown",
        "last_ok": None,
        "last_latency_ms": None,
        "last_error": None,
    }


async def test_record_sinks_called() -> None:
    seen_local: list[ProviderCallRecord] = []
    seen_global: list[ProviderCallRecord] = []

    async def local(record: ProviderCallRecord) -> None:
        seen_local.append(record)

    async def global_sink(record: ProviderCallRecord) -> None:
        seen_global.append(record)

    set_record_sink(global_sink)
    chain: FallbackChain[Fake] = FallbackChain(
        [Fake("a", fail=True), Fake("b")], timeout_s=1, task="llm", on_record=local
    )
    await chain.call("run", "x")
    assert len(seen_local) == 2 and len(seen_global) == 2
    assert all(isinstance(r, ProviderCallRecord) for r in seen_local)
    row = seen_global[0].to_dict()
    assert row["task"] == "llm" and row["provider"] == "a" and row["ok"] is False
    assert isinstance(row["created_at"], str)


async def test_failing_sink_does_not_break_call() -> None:
    async def bad(record: ProviderCallRecord) -> None:
        raise RuntimeError("db down")

    chain: FallbackChain[Fake] = FallbackChain([Fake("a")], timeout_s=1, on_record=bad)
    assert await chain.call("run", "x") == "a:x"


async def test_recent_calls_ring_buffer_newest_first() -> None:
    assert chains_mod._recent.maxlen == 300
    chain: FallbackChain[Fake] = FallbackChain([Fake("a")], timeout_s=1, task="t")
    for i in range(5):
        await chain.call("run", str(i))
    assert len(recent_calls(3)) == 3
    assert [r.ok for r in recent_calls()] == [True] * 5
    assert recent_calls()[0].created_at >= recent_calls()[-1].created_at


async def test_task_defaults_to_fn_name() -> None:
    chain: FallbackChain[Fake] = FallbackChain([Fake("a")], timeout_s=1)
    await chain.call("run", "x")
    assert recent_calls()[0].task == "run"
