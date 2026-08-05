import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import user as user_crud
from app.schemas.user import PublicUserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=PublicUserOut)
def get_public_profile(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """다른 사용자의 공개 프로필 (닉네임, 제보·후기 수). 피드 유저 전용 페이지 헤더용."""
    profile = user_crud.get_public_profile(db, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    user, playground_count, comment_count = profile
    return PublicUserOut(
        id=user.id,
        nickname=user.nickname,
        playground_count=playground_count,
        comment_count=comment_count,
    )
