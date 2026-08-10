import requests

from blog_place_collector.config import (
    AREA_KEYWORD,
    KAKAO_LOCAL_SEARCH_URL,
    KAKAO_SEARCH_RADIUS,
    kakao_auth_headers,
)

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


def _pick_best_match(documents, keyword):
    """정확히 일치하는 상호, 부분 일치 상호, 거리순 결과 순으로 선택합니다."""
    exact = [document for document in documents if document["place_name"] == keyword]
    if exact:
        return exact[0]

    contains = [
        document for document in documents if keyword in document["place_name"]
    ]
    if contains:
        return contains[0]

    return documents[0]


def search_place(
    keyword,
    area_keyword=AREA_KEYWORD,
    radius=KAKAO_SEARCH_RADIUS,
):
    """상호명을 검색해 장소 정보(좌표·주소 등)를 반환합니다."""
    documents = _search_documents(keyword, area_keyword=area_keyword, radius=radius)
    if not documents:
        return None

    place = _pick_best_match(documents, keyword)
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
