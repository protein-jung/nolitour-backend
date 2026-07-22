import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.crud import playground as crud
from app.crud import social as social_crud
from app.models.playground import Playground
from app.models.social import PlaygroundComment
from app.models.user import User
from app.schemas.admin import AdminStats
from app.schemas.playground import PlaygroundOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)])


@router.get("/stats", response_model=AdminStats)
def get_stats(db: Session = Depends(get_db)):
    total_playgrounds = db.execute(select(func.count()).select_from(Playground)).scalar_one()
    pending_playgrounds = db.execute(
        select(func.count()).select_from(Playground).where(Playground.is_verified.is_(False))
    ).scalar_one()
    total_users = db.execute(select(func.count()).select_from(User)).scalar_one()
    total_comments = db.execute(select(func.count()).select_from(PlaygroundComment)).scalar_one()
    return AdminStats(
        total_playgrounds=total_playgrounds,
        pending_playgrounds=pending_playgrounds,
        total_users=total_users,
        total_comments=total_comments,
    )


@router.get("/playgrounds", response_model=list[PlaygroundOut])
def list_playgrounds(is_verified: bool | None = None, db: Session = Depends(get_db)):
    """관리자용 놀이터 목록. is_verified=false 로 검수 대기 목록만 조회 가능."""
    return crud.list_playgrounds_for_admin(db, is_verified=is_verified)


@router.patch("/playgrounds/{playground_id}/verify", response_model=PlaygroundOut)
def verify_playground(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    return crud.verify_playground(db, playground)


@router.delete("/playgrounds/{playground_id}", status_code=204)
def delete_playground(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    crud.delete_playground(db, playground)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: uuid.UUID, db: Session = Depends(get_db)):
    """관리자는 작성자와 무관하게 부적절한 댓글/후기를 삭제할 수 있다."""
    comment = social_crud.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    social_crud.delete_comment(db, comment)
