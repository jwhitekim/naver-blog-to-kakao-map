import requests

from blog_place_collector.config import (
    AREA_KEYWORD,
    KAKAO_FAVORITE_ADD_URL,
    KAKAO_LOCAL_SEARCH_URL,
    KAKAO_SEARCH_RADIUS,
    KAKAO_TRANSCOORD_URL,
    kakao_auth_headers,
    kakao_map_headers,
)

_area_anchor = None


def _get_area_anchor():
    """지역 대표 좌표를 구해 검색 결과의 거리 기준점으로 사용합니다."""
    global _area_anchor
    if _area_anchor is None:
        response = requests.get(
            KAKAO_LOCAL_SEARCH_URL,
            params={"query": AREA_KEYWORD},
            headers=kakao_auth_headers,
            timeout=10,
        )
        response.raise_for_status()
        document = response.json()["documents"][0]
        _area_anchor = (document["x"], document["y"])
    return _area_anchor


def _to_wcongnamul(wgs84_x, wgs84_y):
    """WGS84 좌표를 카카오맵 즐겨찾기 API의 내부 좌표계로 변환합니다."""
    response = requests.get(
        KAKAO_TRANSCOORD_URL,
        params={
            "x": wgs84_x,
            "y": wgs84_y,
            "input_coord": "WGS84",
            "output_coord": "WCONGNAMUL",
        },
        headers=kakao_auth_headers,
        timeout=10,
    )
    response.raise_for_status()
    document = response.json()["documents"][0]
    return document["x"], document["y"]


def _search_documents(keyword, max_pages=3):
    """지역 기준점에서 가까운 장소를 최대 max_pages 페이지까지 조회합니다."""
    anchor_x, anchor_y = _get_area_anchor()
    documents = []
    for page in range(1, max_pages + 1):
        response = requests.get(
            KAKAO_LOCAL_SEARCH_URL,
            params={
                "query": keyword,
                "x": anchor_x,
                "y": anchor_y,
                "radius": KAKAO_SEARCH_RADIUS,
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


def search_place(keyword):
    """상호명을 검색해 즐겨찾기 API에 필요한 장소 데이터로 변환합니다."""
    documents = _search_documents(keyword)
    if not documents:
        return None

    place = _pick_best_match(documents, keyword)
    x, y = _to_wcongnamul(place["x"], place["y"])
    return {
        "type": "place",
        "key": int(place["id"]),
        "display1": place["place_name"],
        "display2": place["road_address_name"] or place["address_name"],
        "x": x,
        "y": y,
        "color": "02",
        "memo": "",
        "folderid": 0,
    }


def add_favorite(place):
    payload = {"datas": [place]}
    response = requests.post(
        KAKAO_FAVORITE_ADD_URL,
        headers=kakao_map_headers,
        json=payload,
        timeout=10,
    )
    print(f"Status Code: {response.status_code}")
    print(response.text)
    return response
