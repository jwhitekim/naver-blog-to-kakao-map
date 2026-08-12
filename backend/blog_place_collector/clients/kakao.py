import re
from difflib import SequenceMatcher

import requests

from blog_place_collector.config import (
    AREA_KEYWORD,
    KAKAO_LOCAL_SEARCH_URL,
    KAKAO_SEARCH_RADIUS,
    kakao_auth_headers,
)

# 카카오맵 웹사이트가 상세 페이지에서 쓰는 비공식 엔드포인트입니다.
# 공식 REST API(키워드 검색)는 영업시간을 제공하지 않아 이걸로 보강합니다.
# 문서화되지 않은 API라 예고 없이 바뀌거나 막힐 수 있습니다.
KAKAO_MAP_OVERALL_URL = "https://map.kakao.com/api/dapi/overall"
_kakao_map_headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://map.kakao.com/",
}

_area_anchors = {}


def _get_area_anchor(area_keyword=AREA_KEYWORD):
    """지역 대표 좌표를 구해 검색 결과의 거리 기준점으로 사용합니다."""
    if area_keyword not in _area_anchors:
        response = requests.get(
            KAKAO_LOCAL_SEARCH_URL,
            params={"query": area_keyword},
            headers=kakao_auth_headers,
            timeout=10,
        )
        response.raise_for_status()
        documents = response.json().get("documents", [])
        if not documents:
            raise ValueError(f"'{area_keyword}' 지역의 기준 좌표를 찾지 못했습니다.")
        document = documents[0]
        _area_anchors[area_keyword] = (document["x"], document["y"])
    return _area_anchors[area_keyword]


def _search_documents(
    keyword,
    area_keyword=AREA_KEYWORD,
    radius=KAKAO_SEARCH_RADIUS,
    max_pages=3,
):
    """지역 기준점에서 가까운 장소를 최대 max_pages 페이지까지 조회합니다."""
    anchor_x, anchor_y = _get_area_anchor(area_keyword)
    documents = []
    for page in range(1, max_pages + 1):
        response = requests.get(
            KAKAO_LOCAL_SEARCH_URL,
            params={
                "query": keyword,
                "x": anchor_x,
                "y": anchor_y,
                "radius": radius,
                "sort": "distance",
                "page": page,
            },
            headers=kakao_auth_headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        documents.extend(data["documents"])
        if data["meta"]["is_end"]:
            break
    return documents


FUZZY_MATCH_THRESHOLD = 0.75


def _normalize_name(text):
    return re.sub(r"\s+", "", text)


def _similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def _names_match(place_name, keyword):
    """부분 문자열이거나(예: '오아시스' / '오아시스 한남점'), 표기가 살짝 달라도
    (오타, 브랜드 수식어 누락, 어순 차이 등) 충분히 비슷하면 같은 상호로 취급합니다."""
    normalized_place = _normalize_name(place_name)
    normalized_keyword = _normalize_name(keyword)
    if normalized_keyword in normalized_place or normalized_place in normalized_keyword:
        return True
    return _similarity(normalized_place, normalized_keyword) >= FUZZY_MATCH_THRESHOLD


def _pick_best_match(documents, keyword, require_match=False):
    """정확히 일치하는 상호, 부분/유사 일치 상호 중 가장 비슷한 것, 거리순 결과 순으로 선택합니다.
    require_match=True면 이름이 전혀 안 맞을 때 거리순 fallback 대신 None을 반환합니다."""
    exact = [document for document in documents if document["place_name"] == keyword]
    if exact:
        return exact[0]

    matches = [
        document for document in documents if _names_match(document["place_name"], keyword)
    ]
    if matches:
        normalized_keyword = _normalize_name(keyword)
        matches.sort(
            key=lambda document: _similarity(
                _normalize_name(document["place_name"]), normalized_keyword
            ),
            reverse=True,
        )
        return matches[0]

    if require_match:
        return None

    return documents[0]


def search_place(
    keyword,
    area_keyword=AREA_KEYWORD,
    radius=KAKAO_SEARCH_RADIUS,
    require_match=False,
):
    """상호명을 검색해 장소 정보(좌표·주소 등)를 반환합니다.
    require_match=True면 이름이 실제로 맞는 결과가 없을 때 None을 반환합니다
    (느슨하게 추출한 후보를 카카오맵 검색으로 검증할 때 사용)."""
    documents = _search_documents(keyword, area_keyword=area_keyword, radius=radius)
    if not documents:
        return None

    place = _pick_best_match(documents, keyword, require_match=require_match)
    if place is None:
        return None
    return {
        "key": int(place["id"]),
        "display1": place["place_name"],
        "display2": place["road_address_name"] or place["address_name"],
        "x": float(place["x"]),
        "y": float(place["y"]),
        "category": place.get("category_name", ""),
        "phone": place.get("phone", ""),
        "place_url": place.get("place_url", ""),
    }


def _extract_business_hours(entry):
    """카카오맵 상세 응답 하나를 화면에 쓸 수 있는 형태로 정리합니다."""
    if not entry:
        return None

    display = entry.get("openhourDisplayText")
    if not display:
        period = next(
            (
                p
                for p in entry.get("periodList") or []
                if p.get("periodName") == "영업기간"
            ),
            None,
        )
        time_list = (period or {}).get("timeList") or []
        if time_list:
            display = time_list[0].get("timeSE")

    if not display:
        return None

    realtime = entry.get("realtime") or {}
    return {
        "display": display,
        "is_open": realtime.get("open") == "Y",
        "closed_today": realtime.get("closedToday") == "Y",
    }


def get_business_hours(place_ids):
    """장소 id 목록의 영업시간을 한 번에 조회합니다(카카오맵 비공식 API)."""
    place_ids = list(place_ids)
    if not place_ids:
        return {}

    response = requests.get(
        KAKAO_MAP_OVERALL_URL,
        params={
            "confirmId": ",".join(str(place_id) for place_id in place_ids),
            "mode": "standard",
        },
        headers=_kakao_map_headers,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    return {
        int(place_id): _extract_business_hours(data.get(str(place_id)))
        for place_id in place_ids
    }
