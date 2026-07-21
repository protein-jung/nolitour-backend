import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import playground as crud
from app.schemas.playground import PlaygroundCreate, PlaygroundOut

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
def create_playground(data: PlaygroundCreate, db: Session = Depends(get_db)):
    """사용자가 직접 놀이터 정보를 등록 (관리자 검수 전까지 is_verified=False)"""
    return crud.create_user_playground(db, data)
