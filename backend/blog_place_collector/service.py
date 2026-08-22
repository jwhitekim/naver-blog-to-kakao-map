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
# 빈약하면(distinct 후보가 적거나 반복 언급이 없음) 자동으로 늘려서 재수집합니다.
PAGE_TIERS = [5, 15, 30]
DEFAULT_RADIUS = 5000
MAX_TOP_N = 30
MIN_CANDIDATES = 10
MIN_REPEAT_MENTION = 2
MIN_REPEATED_CANDIDATES = 5


def _enough_repeat_candidates(candidates):
    """상호명 후보가 "확실한 결과"로 보여줄 만큼 모였는지 판단합니다. 단순히 1등
    후보의 언급 횟수만 보면 "부산여행"처럼 넓은 검색도 우연히 통과해버립니다
    (10개 후보를 채웠는데 1등만 2회, 나머지는 다 1회) — 실측 확인. 그래서 "2회 이상
    언급된 후보가 몇 개나 있는지"로 봅니다. 이 기준을 tier 반복 중단과 최종
    결과/개요 판단에 동일하게 씁니다."""
    repeated = sum(1 for c in candidates if c["mention_count"] >= MIN_REPEAT_MENTION)
    return len(candidates) >= MIN_CANDIDATES and repeated >= MIN_REPEATED_CANDIDATES


def _collect_candidates(keyword):
    """PAGE_TIERS를 시도하며 상호명 후보를 수집·검증합니다. 마지막으로 수집한 posts도
    함께 반환합니다 — 개요로 전환할 때 재수집 없이 그대로 재사용하기 위해서입니다.

    확신 후보(2회 이상 언급)가 최소 기준을 넘겨도, 직전 tier보다 여전히 늘고 있으면
    "더 넓은 지역일 수 있다"고 보고 계속 다음 tier로 진행합니다. 늘지 않거나(정체)
    줄어들면 그 시점에서 멈춥니다 — 좁은 지역명은 tier 1에서 빨리 끝나고, 넓은
    지역명은 신호가 계속 느는 동안 더 많은 글을 모으게 됩니다."""
    candidates = []
    posts = []
    post_count = 0
    previous_confirmed = 0
    for max_pages in PAGE_TIERS:
        posts = naver_blog_search(keyword=keyword, max_pages=max_pages)
        post_count = len(posts)
        if not posts:
            break

        regions = extract_regions(keyword)
        guesses = extract_business_names(posts, keyword)
        candidates = _verified_candidates(guesses, regions=regions, radius=DEFAULT_RADIUS)

        confirmed = sum(1 for c in candidates if c["mention_count"] >= MIN_REPEAT_MENTION)
        if confirmed >= MIN_REPEATED_CANDIDATES and confirmed <= previous_confirmed:
            break
        previous_confirmed = confirmed

    return post_count, posts, candidates


def _finalize_candidates(candidates):
    """확신 후보(2회 이상 언급)를 최대 MAX_TOP_N개까지 모두 보여줍니다. 확신 후보가
    MIN_REPEATED_CANDIDATES에 못 미치면(좁은 검색) 결과가 텅 비어 보이지 않도록
    1회 언급 후보까지 포함해 상위 5개를 채웁니다."""
    confirmed = [c for c in candidates if c["mention_count"] >= MIN_REPEAT_MENTION]
    if len(confirmed) >= MIN_REPEATED_CANDIDATES:
        top_candidates = confirmed[:MAX_TOP_N]
    else:
        top_candidates = candidates[:MIN_REPEATED_CANDIDATES]

    for candidate in top_candidates:
        candidate["naver_search_url"] = f"https://map.naver.com/p/search/{quote(candidate['name'])}"
    _attach_business_hours(top_candidates)
    return top_candidates


def preview_collection(keyword):
    """수집부터 장소 매칭까지 실행하되 즐겨찾기는 변경하지 않습니다.
    지역+카테고리를 이미 확정한 드릴다운 검색에 씁니다(자동판단 없이 곧장 상세 결과)."""
    post_count, _posts, candidates = _collect_candidates(keyword)
    return {"post_count": post_count, "candidates": _finalize_candidates(candidates)}


def search_collection(keyword):
    """검색어 하나로 상세 결과와 지역 개요 중 뭘 보여줄지 자동으로 판단합니다.
    상세 검색(카카오 검증까지)을 먼저 시도하고, 결과가 확실하면 그대로 보여주고,
    빈약하면 이미 수집해둔 글을 재사용해 지역별 개요로 전환합니다."""
    post_count, posts, candidates = _collect_candidates(keyword)

    if not posts or _enough_repeat_candidates(candidates):
        return {
            "mode": "results",
            "post_count": post_count,
            "candidates": _finalize_candidates(candidates),
        }

    regions = extract_region_overview(posts, keyword)
    return {"mode": "overview", "post_count": post_count, "regions": regions}


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
