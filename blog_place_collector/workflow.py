from blog_place_collector.clients.gemini import top_business_names
from blog_place_collector.clients.kakao import add_favorite, search_place
from blog_place_collector.clients.naver import naver_blog_search
from blog_place_collector.config import TOP_N


def run():
    posts = naver_blog_search()
    print(f"\n블로그 포스팅 {len(posts)}건 수집 완료\n")

    candidates = top_business_names(posts, TOP_N)
    print(f"상위 {TOP_N}개 상호명 후보: {candidates}\n")

    for name, count in candidates:
        place = search_place(name)
        if place is None:
            print(f"[스킵] '{name}' ({count}회 언급) - 카카오맵 검색 결과 없음")
            continue

        print(
            f"[등록 시도] '{name}' ({count}회 언급) -> "
            f"{place['display1']} ({place['display2']})"
        )
        add_favorite(place)
        print()
