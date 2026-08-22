import re
from urllib.parse import quote

import requests

from blog_place_collector.clients.gemini import (
    extract_business_names,
    extract_region_overview,
    extract_regions,
)
from blog_place_collector.clients.kakao import get_area_anchor, get_business_hours, search_place
from blog_place_collector.clients.naver import naver_blog_search, naver_local_search

# 사용자가 직접 고르던 값들을 상수로 고정합니다. 대신 수집 페이지 수는 결과가
# 빈약하면(distinct 후보가 적거나 전부 1회 언급) 자동으로 늘려서 재수집합니다.
PAGE_TIERS = [5, 15, 30]
DEFAULT_RADIUS = 5000
DEFAULT_TOP_N = 10
MIN_CANDIDATES = 10
MIN_REGIONS = 3
MIN_TOP_MENTION = 2


def _has_enough_signal(items, min_items, min_top_mention):
    """items가 충분히 모였는지 판단합니다. candidates(상호명 카드)와 regions(개요)
    둘 다 mention_count 필드를 가지므로 그대로 재사용합니다."""
    return len(items) >= min_items and items and items[0]["mention_count"] >= min_top_mention


def overview_collection(keyword):
    """넓은 여행 키워드를 지역별 카테고리 구조(언급 빈도 포함)로 정리합니다.
    상호명은 뽑지 않습니다 — 사용자가 지역+카테고리를 고르면 preview_collection으로 넘어갑니다."""
    regions = []
    post_count = 0
    for max_pages in PAGE_TIERS:
        posts = naver_blog_search(keyword=keyword, max_pages=max_pages)
        post_count = len(posts)
        if not posts:
            break

        regions = extract_region_overview(posts, keyword)
        if _has_enough_signal(regions, MIN_REGIONS, MIN_TOP_MENTION):
            break

    return {"post_count": post_count, "regions": regions}


def preview_collection(keyword):
    """수집부터 장소 매칭까지 실행하되 즐겨찾기는 변경하지 않습니다."""
    candidates = []
    post_count = 0
    for max_pages in PAGE_TIERS:
        posts = naver_blog_search(keyword=keyword, max_pages=max_pages)
        post_count = len(posts)
        if not posts:
            break

        regions = extract_regions(keyword)
        guesses = extract_business_names(posts, keyword)
        candidates = _verified_candidates(guesses, regions=regions, radius=DEFAULT_RADIUS)
        if _has_enough_signal(candidates, MIN_CANDIDATES, MIN_TOP_MENTION):
            break

    top_candidates = candidates[:DEFAULT_TOP_N]

    for candidate in top_candidates:
        candidate["naver_search_url"] = f"https://map.naver.com/p/search/{quote(candidate['name'])}"

    _attach_business_hours(top_candidates)

    return {
        "post_count": post_count,
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

    candidates = [grouped[key] for key in order]
    return _sort_candidates(candidates, regions)


def _sort_candidates(candidates, regions):
    """언급 횟수가 많은 순으로 정렬합니다. 언급 횟수가 같으면, 검색 지역 기준점(첫
    번째로 감지된 지역)에서 가까운 곳을 우선합니다. 지역 정보가 없으면 동점은
    먼저 검증된 순서 그대로 둡니다."""
    anchor = None
    if regions:
        try:
            anchor = get_area_anchor(regions[0])
        except ValueError:
            anchor = None

    def sort_key(candidate):
        if anchor is None:
            return (-candidate["mention_count"], 0)
        distance = _distance_sq(candidate["place"]["x"], candidate["place"]["y"], *anchor)
        return (-candidate["mention_count"], distance)

    candidates.sort(key=sort_key)
    return candidates


def _distance_sq(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2


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

    return search_place(name, require_match=True, nationwide=True, regions=regions)


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
