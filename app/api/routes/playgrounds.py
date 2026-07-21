import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.storage import get_storage_backend
from app.crud import playground as crud
from app.models.playground import PlaygroundImage
from app.models.user import User
from app.schemas.playground import PlaygroundCreate, PlaygroundImageOut, PlaygroundOut

router = APIRouter(prefix="/playgrounds", tags=["playgrounds"])


@router.get("", response_model=list[PlaygroundOut])
def list_playgrounds(
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lng: float | None = None,
    max_lng: float | None = None,
    db: Session = Depends(get_db),
):
    """지도 bounding box 기준으로 놀이터 목록 조회"""
    return crud.list_playgrounds(
        db, min_lat=min_lat, max_lat=max_lat, min_lng=min_lng, max_lng=max_lng
    )


@router.get("/{playground_id}", response_model=PlaygroundOut)
def get_playground(playground_id: uuid.UUID, db: Session = Depends(get_db)):
    playground = crud.get_playground(db, playground_id)
    if playground is None:
        raise HTTPException(status_code=404, detail="Playground not found")
    return playground


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
