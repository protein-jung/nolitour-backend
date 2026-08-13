import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional, get_viewer_key
from app.core.geo import haversine_distance_m
from app.core.storage import get_storage_backend
from app.crud import playground as crud
from app.crud import social as social_crud
from app.models.playground import AgeGroup, EquipmentType, PlaygroundImage
from app.models.social import CommentReply, PlaygroundComment
from app.models.user import User
from app.schemas.playground import (
    PlaygroundCreate,
    PlaygroundEditOut,
    PlaygroundImageOut,
    PlaygroundOut,
    PlaygroundUpdate,
    VisitCheckIn,
    VisitResult,
)
from app.schemas.social import (
    CommentCreate,
    CommentImageOut,
    CommentOut,
    CommentReplyCreate,
    CommentReplyOut,
    LikeStatus,
    MyReviewOut,
    MyVisitOut,
    SaveStatus,
)

VISIT_RADIUS_M = 300

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
        images=list(comment.images),
    )


def _reply_out(reply: CommentReply) -> CommentReplyOut:
    return CommentReplyOut(
        id=reply.id,
        content=reply.content,
        created_at=reply.created_at,
        author_nickname=reply.author.nickname,
        author_id=reply.user_id,
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
    is_free: bool = False,
    has_cctv: bool = False,
    has_fence: bool = False,
    stroller_friendly: bool = False,
    pet_friendly: bool = False,
    equipment: list[EquipmentType] | None = Query(default=None),
    sort: str | None = None,
    limit: int = Query(default=500, le=500),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """지도 bounding box + 필터 조건으로 놀이터 목록 조회. sort="popular"면 인기 점수순으로 정렬."""
    playgrounds = crud.list_playgrounds(
        db,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        age_groups=age_group,
        has_shade=has_shade,
        has_parking=has_parking,
        has_restroom=has_restroom,
        is_free=is_free,
        has_cctv=has_cctv,
        has_fence=has_fence,
        stroller_friendly=stroller_friendly,
        pet_friendly=pet_friendly,
        equipment=equipment,
        sort=sort,
        limit=limit,
    )
    reviewed_ids = social_crud.list_reviewed_playground_ids(db, current_user.id) if current_user else set()
    visited_ids = social_crud.list_visited_playground_ids(db, current_user.id) if current_user else set()
    active_viewer_counts = crud.get_active_viewer_counts(db, [p.id for p in playgrounds])
    result = []
    for p in playgrounds:
        out = PlaygroundOut.model_validate(p)
        out.reviewed_by_me = p.id in reviewed_ids
        out.visited_by_me = p.id in visited_ids
        out.active_viewers = active_viewer_counts.get(p.id, 0)
        result.append(out)
    return result


@router.get("/mine", response_model=list[PlaygroundOut])
def list_my_playgrounds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내가 제보한 놀이터 목록 (마이페이지용)"""
    return crud.list_playgrounds_by_submitter(db, current_user.id)


@router.get("/mine/visits", response_model=list[MyVisitOut])
def list_my_visits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내가 GPS 체크인('왔다감')한 놀이터 기록 (놀이터캘린더용)"""
    rows = social_crud.list_visits_by_user(db, current_user.id)
    return [
        MyVisitOut(
            id=v.id,
            playground_id=v.playground_id,
            playground_name=name,
            playground_image_url=image_url,
            created_at=v.created_at,
        )
        for v, name, image_url in rows
    ]


@router.get("/mine/reviews", response_model=list[MyReviewOut])
def list_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내가 작성한 댓글·후기 목록 (놀이터캘린더용)"""
    rows = social_crud.list_comments_by_user(db, current_user.id)
    return [
        MyReviewOut(
            id=c.id,
            playground_id=c.playground_id,
            playground_name=name,
            content=c.content,
            rating=c.rating,
            created_at=c.created_at,
        )
        for c, name in rows
    ]


@router.get("/{playground_id}", response_model=PlaygroundOut)
def get_playground(
    playground_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    viewer_key: str | None = Depends(get_viewer_key),
):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")

    crud.record_view(db, playground, current_user.id if current_user else None, viewer_key)

    like_count, liked_by_me = social_crud.get_like_status(
        db, playground_id, current_user.id if current_user else None
    )
    save_count, saved_by_me = social_crud.get_save_status(
        db, playground_id, current_user.id if current_user else None
    )
    comment_count = len(social_crud.list_comments(db, playground_id))
    average_rating, rating_count = social_crud.get_rating_stats(db, playground_id)

    out = PlaygroundOut.model_validate(playground)
    out.like_count = like_count
    out.liked_by_me = liked_by_me
    out.save_count = save_count
    out.saved_by_me = saved_by_me
    out.comment_count = comment_count
    out.average_rating = average_rating
    out.rating_count = rating_count
    out.active_viewers = crud.get_active_viewer_counts(db, [playground_id]).get(playground_id, 0)
    if current_user:
        out.reviewed_by_me = playground_id in social_crud.list_reviewed_playground_ids(db, current_user.id)
        out.visited_by_me = playground_id in social_crud.list_visited_playground_ids(db, current_user.id)
    return out


@router.post("", response_model=PlaygroundOut, status_code=201)
def create_playground(
    data: PlaygroundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """로그인한 사용자가 직접 놀이터 정보를 제보 (관리자 검수 전까지 is_verified=False)"""
    return crud.create_user_playground(db, data, submitted_by_id=current_user.id)


@router.patch("/{playground_id}", response_model=PlaygroundOut)
def update_playground(
    playground_id: uuid.UUID,
    data: PlaygroundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """로그인한 사용자 누구나 기존 놀이터 정보를 수정할 수 있다 (나무위키 스타일).
    바뀐 필드는 자동으로 수정 이력에 기록된다."""
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    playground = crud.update_playground(db, playground, data, editor_id=current_user.id)

    like_count, liked_by_me = social_crud.get_like_status(db, playground_id, current_user.id)
    save_count, saved_by_me = social_crud.get_save_status(db, playground_id, current_user.id)
    comment_count = len(social_crud.list_comments(db, playground_id))
    average_rating, rating_count = social_crud.get_rating_stats(db, playground_id)

    out = PlaygroundOut.model_validate(playground)
    out.like_count = like_count
    out.liked_by_me = liked_by_me
    out.save_count = save_count
    out.saved_by_me = saved_by_me
    out.comment_count = comment_count
    out.average_rating = average_rating
    out.rating_count = rating_count
    out.active_viewers = crud.get_active_viewer_counts(db, [playground_id]).get(playground_id, 0)
    out.reviewed_by_me = playground_id in social_crud.list_reviewed_playground_ids(db, current_user.id)
    out.visited_by_me = playground_id in social_crud.list_visited_playground_ids(db, current_user.id)
    return out


@router.get("/{playground_id}/edits", response_model=list[PlaygroundEditOut])
def get_playground_edits(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    """놀이터 정보 수정 이력 (누가 무엇을 언제 바꿨는지)"""
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    logs = crud.list_edit_logs(db, playground_id)
    return [
        PlaygroundEditOut(
            id=log.id,
            editor_id=log.editor_id,
            editor_nickname=log.editor.nickname,
            changes=log.changes,
            created_at=log.created_at,
        )
        for log in logs
    ]


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


@router.post("/{playground_id}/save", response_model=SaveStatus, status_code=201)
def save_playground(
    playground_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """놀이터를 저장(북마크)한다. 좋아요와 별개로 나중에 다시 보기 위한 용도."""
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    social_crud.save_playground(db, playground_id, current_user.id)
    save_count, saved_by_me = social_crud.get_save_status(db, playground_id, current_user.id)
    return SaveStatus(save_count=save_count, saved_by_me=saved_by_me)


@router.delete("/{playground_id}/save", response_model=SaveStatus)
def unsave_playground(
    playground_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if crud.get_playground(db, playground_id) is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    social_crud.unsave_playground(db, playground_id, current_user.id)
    save_count, saved_by_me = social_crud.get_save_status(db, playground_id, current_user.id)
    return SaveStatus(save_count=save_count, saved_by_me=saved_by_me)


@router.post("/{playground_id}/visit", response_model=VisitResult, status_code=201)
def check_in_playground(
    playground_id: uuid.UUID,
    data: VisitCheckIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GPS 위치를 확인해 놀이터 근처에 있을 때만 '왔다감' 체크인을 기록한다."""
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")

    distance_m = haversine_distance_m(
        data.latitude, data.longitude, playground.latitude, playground.longitude
    )
    if distance_m > VISIT_RADIUS_M:
        raise HTTPException(
            status_code=400,
            detail=f"놀이터에서 {int(distance_m)}m 떨어져 있어요. {VISIT_RADIUS_M}m 이내에서 체크인할 수 있어요.",
        )

    social_crud.create_visit(db, playground_id, current_user.id)
    return VisitResult(visited_by_me=True, distance_m=distance_m)


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


@router.post(
    "/{playground_id}/comments/{comment_id}/images", response_model=CommentImageOut, status_code=201
)
def upload_comment_image(
    playground_id: uuid.UUID,
    comment_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """후기 작성자가 후기에 사진을 추가한다."""
    comment = social_crud.get_comment(db, comment_id)
    if comment is None or comment.playground_id != playground_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 후기에만 사진을 추가할 수 있습니다.")

    image_url = get_storage_backend().save(file, folder=f"comments/{comment_id}")
    return social_crud.add_comment_image(db, comment_id, image_url)


@router.post(
    "/{playground_id}/comments/{comment_id}/like", response_model=LikeStatus, status_code=201
)
def like_comment(
    playground_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """다른 사람의 후기(피드 게시물)에 좋아요를 남긴다."""
    comment = social_crud.get_comment(db, comment_id)
    if comment is None or comment.playground_id != playground_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    social_crud.like_comment(db, comment_id, current_user.id)
    like_count, liked_by_me = social_crud.get_comment_like_status(db, comment_id, current_user.id)
    return LikeStatus(like_count=like_count, liked_by_me=liked_by_me)


@router.delete("/{playground_id}/comments/{comment_id}/like", response_model=LikeStatus)
def unlike_comment(
    playground_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = social_crud.get_comment(db, comment_id)
    if comment is None or comment.playground_id != playground_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    social_crud.unlike_comment(db, comment_id, current_user.id)
    like_count, liked_by_me = social_crud.get_comment_like_status(db, comment_id, current_user.id)
    return LikeStatus(like_count=like_count, liked_by_me=liked_by_me)


@router.get("/{playground_id}/comments/{comment_id}/replies", response_model=list[CommentReplyOut])
def get_comment_replies(playground_id: uuid.UUID, comment_id: uuid.UUID, db: Session = Depends(get_db)):
    comment = social_crud.get_comment(db, comment_id)
    if comment is None or comment.playground_id != playground_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    replies = social_crud.list_comment_replies(db, comment_id)
    return [_reply_out(r) for r in replies]


@router.post(
    "/{playground_id}/comments/{comment_id}/replies", response_model=CommentReplyOut, status_code=201
)
def post_comment_reply(
    playground_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: CommentReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """다른 사람의 후기(피드 게시물)에 답글을 남긴다."""
    comment = social_crud.get_comment(db, comment_id)
    if comment is None or comment.playground_id != playground_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    reply = social_crud.create_comment_reply(db, comment_id, current_user.id, data.content)
    return _reply_out(reply)


@router.delete("/{playground_id}/comments/{comment_id}/replies/{reply_id}", status_code=204)
def remove_comment_reply(
    playground_id: uuid.UUID,
    comment_id: uuid.UUID,
    reply_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reply = social_crud.get_comment_reply(db, reply_id)
    if reply is None or reply.comment_id != comment_id:
        raise HTTPException(status_code=404, detail="Reply not found")
    if reply.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 답글만 삭제할 수 있습니다.")
    social_crud.delete_comment_reply(db, reply)


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
