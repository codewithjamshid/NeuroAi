"""Telegram link codes, background `/start <code>` poller, red-flag fan-out (TZ §6.2, M8)."""

import asyncio
import contextlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.hooks import register_shutdown, register_startup
from app.db.session import get_sessionmaker
from app.modules.notifications import templates_uz
from app.modules.notifications.telegram import TelegramClient, TelegramError
from app.modules.patients.models import Caregiver, Patient, RedFlag
from app.modules.users.models import Notification, User

log = logging.getLogger("neuroai.notifications")

CODE_TTL = timedelta(minutes=15)
POLL_INTERVAL_S = 3.0
LOCAL_TZ = ZoneInfo("Asia/Samarkand")

_codes: dict[str, tuple[uuid.UUID, datetime]] = {}
_bot_username: str | None = None
_offset: int | None = None


def get_client(settings: Settings | None = None) -> TelegramClient:
    return TelegramClient((settings or get_settings()).telegram_bot_token)


# --- link codes ------------------------------------------------------------------------------


def _purge_codes(now: datetime) -> None:
    for code in [c for c, (_, exp) in _codes.items() if exp <= now]:
        _codes.pop(code, None)


def create_link_code(user_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    _purge_codes(now)
    for code, (uid, _) in list(_codes.items()):
        if uid == user_id:
            _codes.pop(code, None)
    while True:
        code = f"{secrets.randbelow(1_000_000):06d}"
        if code not in _codes:
            break
    _codes[code] = (user_id, now + CODE_TTL)
    return code


def consume_link_code(code: str) -> uuid.UUID | None:
    _purge_codes(datetime.now(UTC))
    entry = _codes.pop(code.strip(), None)
    return entry[0] if entry else None


async def bot_username(settings: Settings | None = None) -> str | None:
    global _bot_username
    if _bot_username:
        return _bot_username
    client = get_client(settings)
    if not client.configured:
        return None
    try:
        me = await client.get_me()
        _bot_username = me.get("username")
    except Exception as exc:
        log.warning("telegram getMe failed", extra={"error": type(exc).__name__})
    return _bot_username


async def link_status(user: User) -> dict[str, Any]:
    chat = user.telegram_chat_id
    return {"linked": bool(chat), "chat_id_masked": f"…{chat[-3:]}" if chat else None}


# --- poller ----------------------------------------------------------------------------------


async def handle_update(update: dict[str, Any], client: TelegramClient) -> bool:
    """`/start <code>` → bind users.telegram_chat_id. Returns True when a user was linked."""
    message = update.get("message") or {}
    text = str(message.get("text") or "").strip()
    chat_id = (message.get("chat") or {}).get("id")
    if chat_id is None or not text.startswith("/start"):
        return False
    parts = text.split(maxsplit=1)
    code = parts[1].strip() if len(parts) > 1 else ""
    user_id = consume_link_code(code) if code else None
    if user_id is None:
        with contextlib.suppress(Exception):
            await client.send_message(chat_id, templates_uz.link_bad())
        return False
    async with get_sessionmaker()() as db:
        user = await db.get(User, user_id)
        if user is None:
            return False
        user.telegram_chat_id = str(chat_id)
        await db.commit()
        full_name = user.full_name
    with contextlib.suppress(Exception):
        await client.send_message(chat_id, templates_uz.link_ok(full_name))
    log.info("telegram linked", extra={"user_id": str(user_id)})
    return True


async def poll_once(client: TelegramClient) -> int:
    global _offset
    updates = await client.get_updates(offset=_offset, long_poll_s=0)
    for update in updates:
        _offset = int(update.get("update_id", 0)) + 1
        try:
            await handle_update(update, client)
        except Exception:
            log.exception("telegram update failed")
    return len(updates)


async def _poll_loop(client: TelegramClient) -> None:
    try:
        await client.delete_webhook()
    except Exception as exc:
        log.warning("telegram deleteWebhook failed", extra={"error": str(exc)[:200]})
    while True:
        try:
            await poll_once(client)
        except asyncio.CancelledError:
            raise
        except (TelegramError, Exception) as exc:  # network / 409 conflict: keep going
            log.warning("telegram poll failed", extra={"error": str(exc)[:200]})
        await asyncio.sleep(POLL_INTERVAL_S)


@register_startup
async def start_poller(app: Any) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        log.info("telegram poller disabled (no token)")
        return
    client = get_client(settings)
    app.state.telegram_poller = asyncio.create_task(_poll_loop(client), name="telegram-poller")
    asyncio.create_task(bot_username(settings))


@register_shutdown
async def stop_poller(app: Any) -> None:
    task = getattr(app.state, "telegram_poller", None)
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await task


# --- notifications ---------------------------------------------------------------------------


async def list_notifications(db: AsyncSession, user: User, limit: int) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return list((await db.scalars(stmt)).all())


async def _recipients(db: AsyncSession, patient: Patient) -> list[User]:
    stmt = (
        select(User)
        .join(Caregiver, Caregiver.user_id == User.id)
        .where(Caregiver.patient_id == patient.id, User.is_active.is_(True))
    )
    users = list((await db.scalars(stmt)).all())
    if patient.clinician_id and all(u.id != patient.clinician_id for u in users):
        clinician = await db.get(User, patient.clinician_id)
        if clinician is not None and clinician.is_active:
            users.append(clinician)
    return users


async def notify(
    db: AsyncSession,
    patient: Patient,
    flag: RedFlag | None,
    category: str,
    severity: str,
    evidence: str | None,
    *,
    settings: Settings | None = None,
) -> list[Notification]:
    """Fan a red flag out to caregivers + clinician. Never raises into the request path."""
    settings = settings or get_settings()
    rows: list[Notification] = []
    try:
        now = datetime.now(UTC)
        text = templates_uz.red_flag_message(
            category,
            severity,
            patient.full_name,
            evidence,
            now.astimezone(LOCAL_TZ).strftime("%H:%M"),
        )
        client = get_client(settings)
        sent_to: list[str] = []
        for user in await _recipients(db, patient):
            payload: dict[str, Any] = {
                "flag_id": str(flag.id) if flag else None,
                "patient_id": str(patient.id),
                "category": category,
                "severity": severity,
                "text": text,
            }
            channel, status = "inapp", "sent"
            if user.telegram_chat_id:
                channel = "telegram"
                if not client.configured:
                    status = "skipped"
                else:
                    try:
                        await client.send_message(user.telegram_chat_id, text)
                        sent_to.append(str(user.id))
                    except Exception as exc:
                        status = "failed"
                        payload["error"] = str(exc)[:200]
                        log.warning("telegram send failed", extra={"error": str(exc)[:200]})
            rows.append(
                Notification(
                    user_id=user.id,
                    channel=channel,
                    kind="red_flag",
                    payload=payload,
                    status=status,
                    sent_at=now if status == "sent" else None,
                )
            )
        db.add_all(rows)
        if flag is not None:
            flag.notified = {
                "at": now.isoformat(),
                "telegram": sent_to,
                "recipients": [str(r.user_id) for r in rows],
            }
        await db.commit()
    except Exception:
        log.exception("notify failed")
        with contextlib.suppress(Exception):
            await db.rollback()
    return rows
