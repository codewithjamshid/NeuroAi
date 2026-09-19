"""ProviderCallRecord → `provider_calls` row. Own AsyncSession per record; never raises."""

import logging
from typing import Any

from app.ai.chains import set_record_sink
from app.ai.providers.base import ProviderCallRecord
from app.core.hooks import register_shutdown, register_startup
from app.db.session import get_sessionmaker
from app.modules.users.models import ProviderCall

log = logging.getLogger("neuroai.observability")


async def provider_call_sink(record: ProviderCallRecord) -> None:
    try:
        async with get_sessionmaker()() as db:
            db.add(
                ProviderCall(
                    provider=record.provider[:32],
                    task=record.task[:32],
                    latency_ms=record.latency_ms,
                    ok=record.ok,
                    fallback_index=record.fallback_index,
                    error=record.error,
                )
            )
            await db.commit()
    except Exception as exc:  # observability must never break a request
        log.debug("provider_calls insert failed: %s", type(exc).__name__)


@register_startup
def install_sink(app: Any) -> None:
    set_record_sink(provider_call_sink)


@register_shutdown
def remove_sink(app: Any) -> None:
    set_record_sink(None)
