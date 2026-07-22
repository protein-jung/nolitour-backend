import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.playground import Playground
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


def list_users_for_admin(db: Session) -> list[tuple[User, int]]:
    """(사용자, 제보한 놀이터 수) 목록을 가입일 최신순으로 반환한다."""
    count_col = func.count(Playground.id)
    stmt = (
        select(User, count_col.label("playground_count"))
        .outerjoin(Playground, Playground.submitted_by_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def set_user_admin(db: Session, user: User, is_admin: bool) -> User:
    user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    return user
