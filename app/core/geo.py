import math

EARTH_RADIUS_M = 6_371_000


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 거리(미터)를 하버사인 공식으로 계산한다."""
    lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return EARTH_RADIUS_M * 2 * math.asin(math.sqrt(a))
