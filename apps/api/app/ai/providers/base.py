"""Shared provider errors + the `provider_calls` row shape (TZ §4.4, §4.5)."""

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class ProviderError(Exception):
    """One provider call failed (network, refusal, bad output); the chain moves on."""


class ProviderTimeout(ProviderError):
    """The provider did not answer within `timeout_s`."""


class ProviderUnavailable(ProviderError):
    """Every provider failed or was skipped (UI: "Eshitolmadim, matn bilan yozing")."""

    def __init__(self, task: str, message: str | None = None) -> None:
        super().__init__(message or f"no provider available for task '{task}'")
        self.task = task


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class ProviderCallRecord:
    """One attempt inside a FallbackChain; persisted to `provider_calls` by the record sink."""

    provider: str
    task: str
    latency_ms: int
    ok: bool
    fallback_index: int
    error: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data
