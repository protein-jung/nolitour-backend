# nolitour-backend

놀이투어(Nolitour) API 서버 — FastAPI + PostgreSQL

## 로컬 개발 환경 세팅

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # 값 채우기

docker compose up -d  # 로컬 Postgres 실행

alembic revision --autogenerate -m "init"
alembic upgrade head

uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

## 프로젝트 구조

```
app/
  core/       # 설정, DB 세션
  models/     # SQLAlchemy 모델
  schemas/    # Pydantic 스키마
  crud/       # DB 접근 로직
  api/routes/ # FastAPI 라우터
alembic/      # DB 마이그레이션
```

## 데이터 소스

- 1차: 공공데이터포털(data.go.kr) 전국 어린이놀이시설 정보
- 2차: 사용자 직접 입력 (`source=user_submitted`, 관리자 검수 전 `is_verified=false`)
