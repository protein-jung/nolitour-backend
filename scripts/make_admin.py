"""휴대폰 번호로 특정 사용자를 관리자로 승격한다.

의도적으로 API가 아닌 CLI 스크립트로만 제공한다 (관리자 승격 엔드포인트는 없음).
사용법: python -m scripts.make_admin 01012345678
"""

import sys

from app.core.database import SessionLocal
from app.crud.user import get_user_by_phone


def main() -> None:
    if len(sys.argv) != 2:
        print("사용법: python -m scripts.make_admin <휴대폰번호>")
        sys.exit(1)

    phone = sys.argv[1].replace("-", "").strip()
    db = SessionLocal()
    try:
        user = get_user_by_phone(db, phone)
        if user is None:
            print(f"휴대폰 번호 {phone} 로 등록된 사용자가 없습니다.")
            sys.exit(1)
        if user.is_admin:
            print(f"{user.nickname} ({phone}) 은(는) 이미 관리자입니다.")
            return
        user.is_admin = True
        db.commit()
        print(f"{user.nickname} ({phone}) 을(를) 관리자로 승격했습니다.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
