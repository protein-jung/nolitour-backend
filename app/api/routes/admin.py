import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.crud import playground as crud
from app.crud import social as social_crud
from app.crud import user as user_crud
from app.models.playground import Playground
from app.models.social import PlaygroundComment
from app.models.user import User
from app.schemas.admin import AdminStats, AdminUserOut, AdminUserUpdate, UserActivity, UserActivityComment
from app.schemas.playground import PlaygroundOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)])


def _admin_user_out(user: User, playground_count: int) -> AdminUserOut:
    return AdminUserOut(
        id=user.id,
        phone=user.phone,
        name=user.name,
        nickname=user.nickname,
        is_admin=user.is_admin,
        created_at=user.created_at,
        playground_count=playground_count,
    )


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
    """관리자용 놀이터 목록. is_verified 생략 시 전체, true/false 로 필터링."""
    return crud.list_playgrounds_for_admin(db, is_verified=is_verified)


@router.patch("/playgrounds/{playground_id}/verify", response_model=PlaygroundOut)
def verify_playground(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    return crud.verify_playground(db, playground)


@router.patch("/playgrounds/{playground_id}/unverify", response_model=PlaygroundOut)
def unverify_playground(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    return crud.unverify_playground(db, playground)


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


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db)):
    rows = user_crud.list_users_for_admin(db)
    return [_admin_user_out(u, count) for u, count in rows]


@router.patch("/users/{user_id}/admin", response_model=AdminUserOut)
def update_user_admin(user_id: uuid.UUID, data: AdminUserUpdate, db: Session = Depends(get_db)):
    """다른 회원의 관리자 권한을 부여/해제한다 (이미 관리자만 호출 가능)."""
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updated = user_crud.set_user_admin(db, user, data.is_admin)
    playground_count = len(crud.list_playgrounds_by_submitter(db, updated.id))
    return _admin_user_out(updated, playground_count)


@router.get("/users/{user_id}/activity", response_model=UserActivity)
def get_user_activity(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """회원 상세: 등록한 놀이터, 작성한 댓글·후기, 좋아요한 놀이터를 한번에 조회한다."""
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    submitted = crud.list_playgrounds_by_submitter(db, user_id)
    comments = social_crud.list_comments_by_user(db, user_id)
    liked = social_crud.list_liked_playgrounds_by_user(db, user_id)

    return UserActivity(
        user=_admin_user_out(user, len(submitted)),
        submitted_playgrounds=submitted,
        comments=[
            UserActivityComment(
                id=c.id,
                content=c.content,
                rating=c.rating,
                created_at=c.created_at,
                playground_id=c.playground_id,
                playground_name=name,
            )
            for c, name in comments
        ],
        liked_playgrounds=liked,
    )
