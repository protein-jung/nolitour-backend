import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.storage import get_storage_backend
from app.crud import playground as crud
from app.crud import social as social_crud
from app.models.playground import AgeGroup, EquipmentType, PlaygroundImage
from app.models.social import PlaygroundComment
from app.models.user import User
from app.schemas.playground import PlaygroundCreate, PlaygroundImageOut, PlaygroundOut
from app.schemas.social import CommentCreate, CommentOut, LikeStatus

router = APIRouter(prefix="/playgrounds", tags=["playgrounds"])


def _comment_out(comment: PlaygroundComment) -> CommentOut:
    return CommentOut(
        id=comment.id,
        content=comment.content,
        rating=comment.rating,
        recommended_ages=comment.recommended_ages,
        risk_tags=comment.risk_tags,
        created_at=comment.created_at,
        author_nickname=comment.author.nickname,
        author_id=comment.user_id,
    )


@router.get("", response_model=list[PlaygroundOut])
def list_playgrounds(
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lng: float | None = None,
    max_lng: float | None = None,
    age_group: list[AgeGroup] | None = Query(default=None),
    has_shade: bool = False,
    has_parking: bool = False,
    has_restroom: bool = False,
    equipment: list[EquipmentType] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """지도 bounding box + 필터 조건으로 놀이터 목록 조회"""
    return crud.list_playgrounds(
        db,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        age_groups=age_group,
        has_shade=has_shade,
        has_parking=has_parking,
        has_restroom=has_restroom,
        equipment=equipment,
    )


@router.get("/mine", response_model=list[PlaygroundOut])
def list_my_playgrounds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내가 제보한 놀이터 목록 (마이페이지용)"""
    return crud.list_playgrounds_by_submitter(db, current_user.id)


@router.get("/{playground_id}", response_model=PlaygroundOut)
def get_playground(
    playground_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")

    like_count, liked_by_me = social_crud.get_like_status(
        db, playground_id, current_user.id if current_user else None
    )
    comment_count = len(social_crud.list_comments(db, playground_id))
    average_rating, rating_count = social_crud.get_rating_stats(db, playground_id)

    out = PlaygroundOut.model_validate(playground)
    out.like_count = like_count
    out.liked_by_me = liked_by_me
    out.comment_count = comment_count
    out.average_rating = average_rating
    out.rating_count = rating_count
    return out


@router.post("", response_model=PlaygroundOut, status_code=201)
def create_playground(
    data: PlaygroundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """로그인한 사용자가 직접 놀이터 정보를 제보 (관리자 검수 전까지 is_verified=False)"""
    return crud.create_user_playground(db, data, submitted_by_id=current_user.id)


@router.post("/{playground_id}/images", response_model=PlaygroundImageOut, status_code=201)
def upload_playground_image(
    playground_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """놀이터 제보 시 사진을 업로드한다. 저장소는 core.storage 추상화를 통해 이후 S3 등으로 교체 가능."""
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")

    image_url = get_storage_backend().save(file, folder=f"playgrounds/{playground_id}")

    image = PlaygroundImage(
        playground_id=playground_id,
        image_url=image_url,
        is_primary=not playground.images,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.post("/{playground_id}/like", response_model=LikeStatus, status_code=201)
def like_playground(
    playground_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    social_crud.like_playground(db, playground_id, current_user.id)
    like_count, liked_by_me = social_crud.get_like_status(db, playground_id, current_user.id)
    return LikeStatus(like_count=like_count, liked_by_me=liked_by_me)


@router.delete("/{playground_id}/like", response_model=LikeStatus)
def unlike_playground(
    playground_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    social_crud.unlike_playground(db, playground_id, current_user.id)
    like_count, liked_by_me = social_crud.get_like_status(db, playground_id, current_user.id)
    return LikeStatus(like_count=like_count, liked_by_me=liked_by_me)


@router.get("/{playground_id}/comments", response_model=list[CommentOut])
def get_comments(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    comments = social_crud.list_comments(db, playground_id)
    return [_comment_out(c) for c in comments]


@router.post("/{playground_id}/comments", response_model=CommentOut, status_code=201)
def post_comment(
    playground_id: uuid.UUID,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    comment = social_crud.create_comment(
        db,
        playground_id,
        current_user.id,
        data.content,
        rating=data.rating,
        recommended_ages=data.recommended_ages,
        risk_tags=data.risk_tags,
    )
    return _comment_out(comment)


@router.delete("/{playground_id}/comments/{comment_id}", status_code=204)
def remove_comment(
    playground_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = social_crud.get_comment(db, comment_id)
    if comment is None or comment.playground_id != playground_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 삭제할 수 있습니다.")
    social_crud.delete_comment(db, comment)
