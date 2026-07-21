"""전국에 흩어진 테스트용 놀이터 100개를 생성한다.

공공데이터 연동 전, 지도/목록 UI를 확인하기 위한 임시 시드 데이터.
source_id를 SEED- 접두사로 표시해 실제 공공데이터와 구분한다.
"""

import random

from app.core.database import SessionLocal
from app.models.playground import AgeGroup, Playground, PlaygroundSource, PlaygroundType

random.seed(42)

CITIES = [
    ("서울", 37.5665, 126.9780),
    ("부산", 35.1796, 129.0756),
    ("대구", 35.8714, 128.6014),
    ("인천", 37.4563, 126.7052),
    ("광주", 35.1595, 126.8526),
    ("대전", 36.3504, 127.3845),
    ("울산", 35.5384, 129.3114),
    ("세종", 36.4801, 127.2891),
    ("수원", 37.2636, 127.0286),
    ("성남", 37.4201, 127.1265),
    ("고양", 37.6584, 126.8320),
    ("용인", 37.2411, 127.1776),
    ("청주", 36.6424, 127.4890),
    ("전주", 35.8242, 127.1480),
    ("천안", 36.8151, 127.1139),
    ("포항", 36.0190, 129.3435),
    ("창원", 35.2280, 128.6811),
    ("제주", 33.4996, 126.5312),
    ("춘천", 37.8813, 127.7300),
    ("강릉", 37.7519, 128.8761),
]

APARTMENT_NAMES = ["행복", "푸른숲", "이편한세상", "래미안", "자이", "푸르지오", "센트럴파크", "한신", "삼성", "현대"]
PARK_NAMES = ["중앙공원", "시민공원", "생태공원", "체육공원", "문화공원", "가족공원", "물빛공원"]
SCHOOL_NAMES = ["햇살초등학교", "은빛유치원", "꿈나무초등학교", "무지개유치원"]
RIVER_NAMES = ["한내", "실개천", "청계", "안양천", "탄천"]

TYPE_WEIGHTS = [
    (PlaygroundType.APARTMENT, 4),
    (PlaygroundType.NEIGHBORHOOD_PARK, 3),
    (PlaygroundType.CHILDRENS_PARK, 2),
    (PlaygroundType.SCHOOL, 2),
    (PlaygroundType.INDOOR, 1),
    (PlaygroundType.THEME, 1),
    (PlaygroundType.RIVERSIDE, 1),
    (PlaygroundType.INCLUSIVE, 1),
]
TYPE_POOL = [t for t, w in TYPE_WEIGHTS for _ in range(w)]

AGE_GROUP_POOL = list(AgeGroup)


def make_name(playground_type: PlaygroundType, city: str) -> str:
    if playground_type == PlaygroundType.APARTMENT:
        return f"{city}{random.choice(APARTMENT_NAMES)}아파트 놀이터"
    if playground_type in (PlaygroundType.NEIGHBORHOOD_PARK, PlaygroundType.CHILDRENS_PARK):
        return f"{city}{random.choice(PARK_NAMES)} 놀이터"
    if playground_type == PlaygroundType.SCHOOL:
        return f"{random.choice(SCHOOL_NAMES)} 놀이터"
    if playground_type == PlaygroundType.INDOOR:
        return f"{city} 실내놀이터"
    if playground_type == PlaygroundType.THEME:
        return f"{city} 테마놀이터"
    if playground_type == PlaygroundType.RIVERSIDE:
        return f"{random.choice(RIVER_NAMES)} 수변공원 놀이터"
    if playground_type == PlaygroundType.INCLUSIVE:
        return f"{city} 무장애통합 놀이터"
    return f"{city} 놀이터"


def make_playground(index: int) -> Playground:
    city, base_lat, base_lng = random.choice(CITIES)
    lat = base_lat + random.uniform(-0.08, 0.08)
    lng = base_lng + random.uniform(-0.08, 0.08)
    playground_type = random.choice(TYPE_POOL)
    age_groups = random.sample(AGE_GROUP_POOL, k=random.randint(1, 2))

    is_indoor = playground_type == PlaygroundType.INDOOR
    is_apartment = playground_type == PlaygroundType.APARTMENT

    return Playground(
        name=make_name(playground_type, city),
        type=playground_type,
        age_groups=age_groups,
        address=f"{city}시 테스트로 {random.randint(1, 200)}길 {random.randint(1, 50)}",
        directions=f"{random.choice(APARTMENT_NAMES)}아파트 정문에서 도보 3분" if is_apartment else None,
        description="공공데이터 연동 전 UI 확인용 테스트 놀이터입니다.",
        latitude=round(lat, 6),
        longitude=round(lng, 6),
        operating_hours="09:00~18:00" if is_indoor else None,
        closed_days="매주 월요일" if is_indoor else None,
        phone="02-1234-5678" if is_indoor else None,
        source=PlaygroundSource.PUBLIC_DATA,
        source_id=f"SEED-{index:04d}",
        is_verified=True,
    )


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Playground).filter(Playground.source_id.like("SEED-%")).count()
        if existing:
            print(f"이미 시드 데이터 {existing}건이 존재합니다. 건너뜁니다.")
            return

        playgrounds = [make_playground(i) for i in range(1, 101)]
        db.add_all(playgrounds)
        db.commit()
        print(f"{len(playgrounds)}개의 테스트 놀이터를 생성했습니다.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
