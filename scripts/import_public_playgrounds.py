"""행정안전부_전국어린이놀이시설정보서비스(공공데이터포털)에서 놀이시설 데이터를 받아와
기존 놀이터 데이터를 전부 지우고 공공/무료 성격의 시설로 다시 채운다.

식당·학원·교회·의료기관 등 상업/비공개 시설은 제외한다 (개요.txt의
"실내 놀이터는 키즈카페 성격 제외, 무료/공공 시설 위주" 방침에 따름).

사용법: python -m scripts.import_public_playgrounds
"""

import sys
import time

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.playground import EquipmentType, Playground, PlaygroundSource, PlaygroundType

BASE_URL = "https://apis.data.go.kr/1741000/pfc3/getPfctInfo3"
PAGE_SIZE = 1000

# 설치장소코드 중 공공/무료 성격의 시설만 남긴다.
# 제외: A001 목욕장업소, A004 식품접객업소, A006 어린이집, A007 유치원,
#       A008 대규모점포, A009 의료기관, A012 학원, A013 놀이제공영업소(키즈카페),
#       A022 박물관, A023 종교시설 — 모두 상업시설이거나 일반에 공개되지 않는 시설.
INCLUDE_PLACE_CODES = {
    "A002",  # 도로휴게시설
    "A003",  # 도시공원
    "A005",  # 아동복지시설
    "A010",  # 주택단지
    "A011",  # 학교
    "A020",  # 주상복합
    "A030",  # 자연휴양림
    "A031",  # 하천
    "A032",  # 야영장
    "A033",  # 공공도서관
    "A092",  # 육아종합지원센터
    "A093",  # 유아교육진흥원
}

# 설치장소코드가 실제 성격과 다르게 등록된 경우(예: 아파트 상가 안 키즈카페가
# "주택단지"로 등록됨)를 걸러내기 위한 이름 기반 보조 필터.
EXCLUDE_NAME_KEYWORDS = ["키즈카페", "키즈룸", "카페", "스튜디오", "체험관", "패밀리랜드"]

TYPE_BY_PLACE_CODE: dict[str, PlaygroundType] = {
    "A003": PlaygroundType.NEIGHBORHOOD_PARK,
    "A010": PlaygroundType.APARTMENT,
    "A020": PlaygroundType.APARTMENT,
    "A011": PlaygroundType.SCHOOL,
    "A031": PlaygroundType.RIVERSIDE,
}


def fetch_page(client: httpx.Client, page_index: int) -> dict:
    url = f"{BASE_URL}?serviceKey={settings.public_data_api_key}&pageIndex={page_index}&recordCountPerPage={PAGE_SIZE}"
    resp = client.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()["response"]
    if payload["header"]["resultCode"] != "00":
        raise RuntimeError(f"공공데이터 API 오류: {payload['header']}")
    return payload


def to_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def build_playground(item: dict) -> Playground | None:
    if item.get("operYnCdNm") != "운영":
        return None

    place_code = item.get("instlPlaceCd")
    if place_code not in INCLUDE_PLACE_CODES:
        return None

    lat = to_float(item.get("latCrtsVl"))
    lng = to_float(item.get("lotCrtsVl"))
    if lat is None or lng is None:
        return None

    name = (item.get("pfctNm") or "").strip()
    if not name:
        return None
    if any(keyword in name for keyword in EXCLUDE_NAME_KEYWORDS):
        return None

    address = (item.get("ronaAddr") or item.get("lotnoAddr") or "").strip()
    detail = (item.get("ronaDaddr") or "").strip()
    if detail:
        address = f"{address} {detail}".strip()
    if not address:
        return None

    p_type = TYPE_BY_PLACE_CODE.get(place_code, PlaygroundType.ETC)
    if item.get("idrodrCdNm") == "실내":
        p_type = PlaygroundType.INDOOR

    equipment = [EquipmentType.WATER_PLAY] if item.get("wowaStylRideCdNm") == "포함" else None

    return Playground(
        name=name[:200],
        type=p_type,
        address=address[:300],
        latitude=lat,
        longitude=lng,
        equipment=equipment,
        source=PlaygroundSource.PUBLIC_DATA,
        source_id=item.get("pfctSn"),
    )


def main() -> None:
    if not settings.public_data_api_key:
        print("PUBLIC_DATA_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
        sys.exit(1)

    db = SessionLocal()
    client = httpx.Client()
    try:
        deleted = db.query(Playground).delete()
        db.commit()
        print(f"기존 놀이터 {deleted}건 삭제 완료.")

        first = fetch_page(client, 1)
        total_cnt = int(first["body"]["totalCnt"])
        total_pages = (total_cnt + PAGE_SIZE - 1) // PAGE_SIZE
        print(f"공공데이터 총 {total_cnt}건, {total_pages}페이지 조회 시작.")

        seen_source_ids: set[str] = set()
        inserted = 0
        skipped = 0

        def process_items(items: list[dict]) -> None:
            nonlocal inserted, skipped
            for item in items:
                playground = build_playground(item)
                if playground is None or playground.source_id in seen_source_ids:
                    skipped += 1
                    continue
                seen_source_ids.add(playground.source_id)
                db.add(playground)
                inserted += 1

        process_items(first["body"]["items"])

        for page in range(2, total_pages + 1):
            body = fetch_page(client, page)["body"]
            process_items(body["items"])
            if page % 10 == 0 or page == total_pages:
                db.commit()
                print(f"  {page}/{total_pages}페이지 · 저장 {inserted}건 · 제외 {skipped}건")
            time.sleep(0.05)

        db.commit()
        print(f"완료: {inserted}건 저장, {skipped}건 제외(상업시설·좌표없음·중복·미운영 등).")
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    main()
