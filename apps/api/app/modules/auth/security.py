"""bcrypt password hashing + HS256 JWT (access 24h, refresh 30d; claims sub/role/typ)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import get_settings

ACCESS_TTL = timedelta(hours=24)
REFRESH_TTL = timedelta(days=30)
ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    rounds = 4 if get_settings().app_env == "test" else 12  # fast tests, real cost otherwise
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def create_token(user_id: uuid.UUID | str, role: str, typ: TokenType) -> str:
    now = datetime.now(UTC)
    ttl = ACCESS_TTL if typ == "access" else REFRESH_TTL
    payload = {
        "sub": str(user_id),
        "role": role,
        "typ": typ,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, typ: TokenType = "access") -> dict[str, Any]:
    """Returns claims or raises `jwt.PyJWTError` (expired, bad signature, wrong typ)."""
    claims = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    if claims.get("typ") != typ or not claims.get("sub"):
        raise jwt.InvalidTokenError("wrong token type")
    return claims
