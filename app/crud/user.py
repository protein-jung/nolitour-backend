from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()


def get_user_by_nickname(db: Session, nickname: str) -> User | None:
    return db.execute(select(User).where(User.nickname == nickname)).scalar_one_or_none()


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        phone=data.phone,
        name=data.name,
        nickname=data.nickname,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, phone: str, password: str) -> User | None:
    user = get_user_by_phone(db, phone)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
