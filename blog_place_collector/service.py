from blog_place_collector.clients.gemini import top_business_candidates
from blog_place_collector.clients.kakao import search_place
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
        results.append({**candidate, "place": place})

    return {
        "post_count": len(posts),
        "candidates": results,
    }
