import uuid

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.schemas import RegisterIn
from app.modules.auth.security import create_token, decode_token, hash_password, verify_password
from app.modules.patients.models import Caregiver, Patient
from app.modules.users.errors import ConflictError, UnauthorizedError
from app.modules.users.models import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower()))


async def resolve_patient_id(db: AsyncSession, user: User) -> uuid.UUID | None:
    """Patient account → own card; caregiver → primary (else first) linked patient."""
    if user.role == "patient":
        return await db.scalar(select(Patient.id).where(Patient.user_id == user.id))
    if user.role == "caregiver":
        stmt = (
            select(Caregiver.patient_id)
            .where(Caregiver.user_id == user.id)
            .order_by(Caregiver.is_primary.desc(), Caregiver.created_at)
            .limit(1)
        )
        return await db.scalar(stmt)
    return None


def issue_tokens(user: User) -> tuple[str, str]:
    return create_token(user.id, user.role, "access"), create_token(user.id, user.role, "refresh")


async def login(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Email yoki parol noto'g'ri", code="invalid_credentials")
    return user


async def refresh(db: AsyncSession, refresh_token: str) -> User:
    try:
        claims = decode_token(refresh_token, "refresh")
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise UnauthorizedError("Refresh token yaroqsiz") from exc
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Foydalanuvchi topilmadi")
    return user


async def register(db: AsyncSession, data: RegisterIn) -> User:
    if await get_user_by_email(db, data.email):
        raise ConflictError("Bu email allaqachon ro'yxatdan o'tgan", code="email_taken")
    user = User(
        role=data.role,
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        locale=data.locale,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
