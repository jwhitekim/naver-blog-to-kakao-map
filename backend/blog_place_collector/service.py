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

    _attach_business_hours(results)

    return {
        "post_count": len(posts),
        "candidates": results,
    }


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
