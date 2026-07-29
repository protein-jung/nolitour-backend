"""'태성로 130' (경기 광주시 태전동) 인근에 테스트용 놀이터 30개를 생성한다.

지도/리스트 UI에서 거리순 정렬, 근처 밀집 마커 표시를 확인하기 위한 임시 시드 데이터.
source_id를 SEED-TAESEONG- 접두사로 표시해 다른 시드/실제 데이터와 구분한다.
"""

import random

from app.core.database import SessionLocal
from app.models.playground import AgeGroup, Playground, PlaygroundSource, PlaygroundType

random.seed(130)

# 태성로 130 (경기 광주시 태전동) 지오코딩 결과
ANCHOR_LAT = 37.378829
ANCHOR_LNG = 127.226662

APARTMENT_NAMES = [
    "태전자이", "태전푸르지오", "오포한라비발디", "e편한세상 태전", "태전힐스테이트",
    "태전동양", "래미안 태전", "태전2차아이파크", "태전현대", "태전동원로얄듀크",
]
PARK_NAMES = ["태전근린공원", "태전중앙공원", "오포체육공원", "태전생태공원", "곤지암천 수변공원"]
SCHOOL_NAMES = ["태전초등학교", "오포초등학교", "태전유치원", "햇살어린이집"]

TYPE_WEIGHTS = [
    (PlaygroundType.APARTMENT, 5),
    (PlaygroundType.NEIGHBORHOOD_PARK, 3),
    (PlaygroundType.CHILDRENS_PARK, 2),
    (PlaygroundType.SCHOOL, 2),
    (PlaygroundType.INDOOR, 1),
    (PlaygroundType.RIVERSIDE, 1),
]
TYPE_POOL = [t for t, w in TYPE_WEIGHTS for _ in range(w)]

AGE_GROUP_POOL = list(AgeGroup)


def make_name(playground_type: PlaygroundType, index: int) -> str:
    if playground_type == PlaygroundType.APARTMENT:
        return f"{random.choice(APARTMENT_NAMES)} 놀이터"
    if playground_type in (PlaygroundType.NEIGHBORHOOD_PARK, PlaygroundType.CHILDRENS_PARK):
        return f"{random.choice(PARK_NAMES)} 놀이터"
    if playground_type == PlaygroundType.SCHOOL:
        return f"{random.choice(SCHOOL_NAMES)} 놀이터"
    if playground_type == PlaygroundType.INDOOR:
        return f"태전동 실내놀이터 {index}호점"
    if playground_type == PlaygroundType.RIVERSIDE:
        return "곤지암천 수변 놀이터"
    return f"태전동 놀이터 {index}"


def make_playground(index: int) -> Playground:
    # 반경 약 1.5km 이내로 흩뿌린다 (위도 1도 ≈ 111km)
    lat = ANCHOR_LAT + random.uniform(-0.012, 0.012)
    lng = ANCHOR_LNG + random.uniform(-0.015, 0.015)
    playground_type = random.choice(TYPE_POOL)
    age_groups = random.sample(AGE_GROUP_POOL, k=random.randint(1, 2))

    is_indoor = playground_type == PlaygroundType.INDOOR
    is_apartment = playground_type == PlaygroundType.APARTMENT

    return Playground(
        name=make_name(playground_type, index),
        type=playground_type,
        age_groups=age_groups,
        address=f"경기 광주시 태성로 {random.randint(1, 260)}",
        directions=f"{random.choice(APARTMENT_NAMES)} 단지 내" if is_apartment else None,
        description="태성로 130 인근 테스트용 놀이터입니다.",
        latitude=round(lat, 6),
        longitude=round(lng, 6),
        operating_hours="09:00~18:00" if is_indoor else None,
        closed_days="매주 월요일" if is_indoor else None,
        phone="031-1234-5678" if is_indoor else None,
        source=PlaygroundSource.PUBLIC_DATA,
        source_id=f"SEED-TAESEONG-{index:04d}",
        is_verified=True,
    )


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Playground).filter(Playground.source_id.like("SEED-TAESEONG-%")).count()
        if existing:
            print(f"이미 태성로 시드 데이터 {existing}건이 존재합니다. 건너뜁니다.")
            return

        playgrounds = [make_playground(i) for i in range(1, 31)]
        db.add_all(playgrounds)
        db.commit()
        print(f"태성로 130 인근에 테스트 놀이터 {len(playgrounds)}개를 생성했습니다.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
