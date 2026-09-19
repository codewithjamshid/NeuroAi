import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value or " " in value:
        raise ValueError("email noto'g'ri")
    return value


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=72)

    _norm = field_validator("email")(lambda cls, v: _email(v))


class RefreshIn(BaseModel):
    refresh: str


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=1, max_length=200)
    role: Literal["clinician", "caregiver"]
    phone: str | None = None
    locale: str = "uz-Latn"

    _norm = field_validator("email")(lambda cls, v: _email(v))


class UserBrief(BaseModel):
    id: uuid.UUID
    role: str
    full_name: str
    patient_id: uuid.UUID | None = None


class TokenPair(BaseModel):
    access: str
    refresh: str


class LoginOut(TokenPair):
    user: UserBrief


class MeOut(BaseModel):
    id: uuid.UUID
    role: str
    full_name: str
    email: str | None
    locale: str
    patient_id: uuid.UUID | None = None
