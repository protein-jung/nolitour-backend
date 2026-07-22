from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.crud import user as crud
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_phone(db, data.phone):
        raise HTTPException(status_code=400, detail="이미 등록된 휴대폰 번호입니다.")
    if crud.get_user_by_nickname(db, data.nickname):
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")
    return crud.create_user(db, data)


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, data.phone, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="휴대폰 번호 또는 비밀번호가 올바르지 않습니다.")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
