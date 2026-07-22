import re
import uuid

from pydantic import BaseModel, ConfigDict, field_validator

PHONE_PATTERN = re.compile(r"^01[0-9]{8,9}$")


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not PHONE_PATTERN.match(digits):
        raise ValueError("올바른 휴대폰 번호 형식이 아닙니다.")
    return digits


class UserCreate(BaseModel):
    phone: str
    password: str
    name: str
    nickname: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다.")
        return v

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 20):
            raise ValueError("닉네임은 1~20자여야 합니다.")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    name: str
    nickname: str
    is_admin: bool


class LoginRequest(BaseModel):
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone(v)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
