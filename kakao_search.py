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


def _search_documents(keyword, max_pages=3):
    """근접순으로 최대 max_pages 페이지(페이지당 15건)까지 가져옵니다.
    프랜차이즈 지점명(예: "OO역점")이 근처에 몰려있으면 정확히 일치하는
    상호명이 첫 페이지 밖으로 밀려날 수 있어, 여러 페이지를 확보해둡니다."""
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
    """거리보다 상호명 일치를 우선합니다: 정확히 일치 > 이름에 포함 > 그중 가장 가까운 곳."""
    exact = [d for d in documents if d["place_name"] == keyword]
    if exact:
        return exact[0]

    contains = [d for d in documents if keyword in d["place_name"]]
    if contains:
        return contains[0]

    return documents[0]


def search_place(keyword):
    """카카오 로컬 API로 상호명을 검색해 favorite/add에 필요한 형태로 변환합니다.
    동명이인 상호가 여러 지역에 있을 수 있어 AREA_KEYWORD 근방 결과를 우선하고,
    거리보다 상호명이 정확히 일치하는 결과를 우선합니다.
    검색 결과가 없으면 None을 반환합니다."""
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
