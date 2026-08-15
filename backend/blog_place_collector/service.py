import re
from urllib.parse import quote

import requests

from blog_place_collector.clients.gemini import extract_business_names, extract_regions
from blog_place_collector.clients.kakao import get_business_hours, search_place
from blog_place_collector.clients.naver import naver_blog_search, naver_local_search


def preview_collection(keyword, max_pages, top_n, radius):
    """수집부터 장소 매칭까지 실행하되 즐겨찾기는 변경하지 않습니다."""
    posts = naver_blog_search(keyword=keyword, max_pages=max_pages)
    if not posts:
        return {"post_count": 0, "candidates": []}

    regions = extract_regions(keyword)
    guesses = extract_business_names(posts, keyword)
    candidates = _verified_candidates(guesses, regions=regions, radius=radius)
    top_candidates = candidates[:top_n]

    for candidate in top_candidates:
        candidate["naver_search_url"] = f"https://map.naver.com/p/search/{quote(candidate['name'])}"

    _attach_business_hours(top_candidates)

    return {
        "post_count": len(posts),
        "candidates": top_candidates,
    }


def _verified_candidates(guesses, regions, radius):
    """LLM이 느슨하게 추출한 후보를 카카오맵 검색으로 검증합니다.
    실제로 존재하는 장소만 남기고, 카카오맵 장소 ID 기준으로 묶어 언급 횟수 순으로 정렬합니다."""
    grouped = {}
    order = []
    for guess in guesses:
        place = _resolve_place(guess["name"], regions=regions, radius=radius)
        if not place:
            continue

        key = place["key"]
        if key not in grouped:
            grouped[key] = {
                "name": place["display1"],
                "mention_count": 0,
                "sources": [],
                "place": place,
            }
            order.append(key)

        entry = grouped[key]
        entry["mention_count"] += 1
        source = guess["post"]
        if not any(existing["url"] == source["url"] for existing in entry["sources"]):
            entry["sources"].append({"title": source["title"], "url": source["url"]})

    ranked = [grouped[key] for key in order]
    ranked.sort(key=lambda candidate: candidate["mention_count"], reverse=True)
    return ranked


def _resolve_place(name, regions, radius):
    """검색어에서 추출된 지역 각각으로 카카오맵 검증을 시도합니다 (지역이 없으면 이 단계는
    건너뜁니다). 실패하면 네이버 지역검색으로 실제 등록명을 얻어 지역별로 재시도하고,
    그래도 안 되면 지역 제한 없이 전국에서 한 번 더 찾아봅니다."""
    for region in regions:
        place = _search_place_safe(name, area_keyword=region, radius=radius)
        if place:
            return place

    try:
        hits = naver_local_search(name, display=5)
    except requests.RequestException:
        hits = []

    for hit in hits:
        if not _loosely_related(hit["title"], name):
            continue
        for region in regions:
            place = _search_place_safe(hit["title"], area_keyword=region, radius=radius)
            if place:
                return place

    return search_place(name, require_match=True, nationwide=True)


def _search_place_safe(name, area_keyword, radius):
    """지역명이 카카오맵에서 기준 좌표를 못 찾는 경우(예: 없는 지명)에도 전체 검증이
    죽지 않도록 감싸서 호출합니다."""
    try:
        return search_place(name, area_keyword=area_keyword, radius=radius, require_match=True)
    except ValueError:
        return None


def _loosely_related(a, b):
    normalized_a = re.sub(r"\s+", "", a)
    normalized_b = re.sub(r"\s+", "", b)
    return normalized_a in normalized_b or normalized_b in normalized_a


def _attach_business_hours(results):
    """영업시간은 비공식 API라 실패해도 나머지 결과에 영향을 주지 않습니다."""
    place_ids = [r["place"]["key"] for r in results if r["place"]]
    if not place_ids:
        return

    try:
        hours_by_id = get_business_hours(place_ids)
    except requests.RequestException:
        return

    for result in results:
        if result["place"]:
            result["place"]["business_hours"] = hours_by_id.get(result["place"]["key"])
