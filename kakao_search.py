import requests

from config import (
    AREA_KEYWORD,
    KAKAO_LOCAL_SEARCH_URL,
    KAKAO_SEARCH_RADIUS,
    KAKAO_TRANSCOORD_URL,
    kakao_auth_headers,
)

_area_anchor = None


def _get_area_anchor():
    """검색 지역(AREA_KEYWORD)의 대표 좌표를 구해서, 동명이인 상호 중
    이 지역에 가까운 결과를 우선하도록 하는 기준점으로 씁니다."""
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
    """favorite/add가 요구하는 카카오맵 내부 좌표계(WCONGNAMUL)로 변환합니다."""
    response = requests.get(
        KAKAO_TRANSCOORD_URL,
        params={"x": wgs84_x, "y": wgs84_y, "input_coord": "WGS84", "output_coord": "WCONGNAMUL"},
        headers=kakao_auth_headers,
        timeout=10,
    )
    response.raise_for_status()
    document = response.json()["documents"][0]
    return document["x"], document["y"]


def _search_documents(keyword):
    anchor_x, anchor_y = _get_area_anchor()
    response = requests.get(
        KAKAO_LOCAL_SEARCH_URL,
        params={
            "query": keyword,
            "x": anchor_x,
            "y": anchor_y,
            "radius": KAKAO_SEARCH_RADIUS,
            "sort": "distance",
        },
        headers=kakao_auth_headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["documents"]


def search_place(keyword):
    """카카오 로컬 API로 상호명을 검색해 favorite/add에 필요한 형태로 변환합니다.
    동명이인 상호가 여러 지역에 있을 수 있어 AREA_KEYWORD 근방 결과를 우선합니다.
    검색 결과가 없으면 None을 반환합니다."""
    documents = _search_documents(keyword)
    if not documents:
        return None

    place = documents[0]
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
