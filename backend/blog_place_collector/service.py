from urllib.parse import quote

import requests

from blog_place_collector.clients.gemini import top_business_candidates
from blog_place_collector.clients.kakao import get_business_hours, search_place
from blog_place_collector.clients.naver import naver_blog_search


def preview_collection(keyword, max_pages, top_n, radius):
    """수집부터 장소 매칭까지 실행하되 즐겨찾기는 변경하지 않습니다."""
    posts = naver_blog_search(keyword=keyword, max_pages=max_pages)
    if not posts:
        return {"post_count": 0, "candidates": []}

    candidates = top_business_candidates(posts, top_n=top_n)
    area_keyword = keyword.split()[0]

    results = []
    for candidate in candidates:
        place = search_place(
            candidate["name"],
            area_keyword=area_keyword,
            radius=radius,
        )
        naver_search_url = f"https://map.naver.com/p/search/{quote(candidate['name'])}"
        results.append({**candidate, "place": place, "naver_search_url": naver_search_url})

    results = _merge_duplicate_places(results)
    _attach_business_hours(results)

    return {
        "post_count": len(posts),
        "candidates": results,
    }


def _merge_duplicate_places(results):
    """LLM이 같은 장소를 다른 상호명으로 추출해도 카카오맵 장소 ID 기준으로 하나로 합칩니다."""
    merged = {}
    order = []
    for result in results:
        place = result["place"]
        key = place["key"] if place else f"unmatched:{result['name']}"
        if key not in merged:
            merged[key] = result
            order.append(key)
            continue

        existing = merged[key]
        existing["mention_count"] += result["mention_count"]
        existing_urls = {source["url"] for source in existing["sources"]}
        for source in result["sources"]:
            if source["url"] not in existing_urls:
                existing["sources"].append(source)
                existing_urls.add(source["url"])

    merged_results = [merged[key] for key in order]
    merged_results.sort(key=lambda result: result["mention_count"], reverse=True)
    return merged_results


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
