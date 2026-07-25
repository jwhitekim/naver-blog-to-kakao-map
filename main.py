from naver_blog_search import naver_blog_search
from llm_extract import top_cafe_names
from kakao_search import search_place
from kakao_favorite import add_favorite
from config import TOP_N

def main():
    posts = naver_blog_search()
    print(f"\n블로그 포스팅 {len(posts)}건 수집 완료\n")

    candidates = top_cafe_names(posts, TOP_N)
    print(f"상위 {TOP_N}개 카페 후보: {candidates}\n")

    for name, count in candidates:
        # "로투스베이커리"는 카카오맵 검색 API 인덱스에 없어서, 같은 자리에 있는
        # 실제 등록명 "로토스"로 직접 검색합니다.
        search_term = "로토스" if name == "로투스베이커리" else name
        place = search_place(search_term)
        if place is None:
            print(f"[스킵] '{name}' ({count}회 언급) - 카카오맵 검색 결과 없음")
            continue

        print(f"[등록 시도] '{name}' ({count}회 언급) -> {place['display1']} ({place['display2']})")
        add_favorite(place)
        print()


if __name__ == "__main__":
    main()
