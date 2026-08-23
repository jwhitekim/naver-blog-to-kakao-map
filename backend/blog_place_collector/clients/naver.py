import html
import re

import requests

from blog_place_collector.config import (
    KEYWORD,
    MAX_PAGES,
    NAVER_BLOG_SEARCH_URL,
    NAVER_LOCAL_SEARCH_URL,
    naver_open_api_headers,
)

# 공식 API는 한 번 호출에 최대 100개까지 준다(display 상한, 실측 확인).
BLOG_SEARCH_PAGE_SIZE = 100


def _strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def naver_blog_search(keyword=KEYWORD, max_pages=MAX_PAGES):
    """네이버 블로그 검색 공식 API로 글을 모읍니다. max_pages는 기존 비공식
    엔드포인트 시절의 "페이지 수"(7개/페이지) 단위를 그대로 유지합니다 — 이 세션
    내내 여러 임계값을 이 글 수 기준(35/105/210개)으로 실측 보정했기 때문입니다."""
    target_count = max_pages * 7
    posts = []
    start = 1

    while len(posts) < target_count:
        display = min(BLOG_SEARCH_PAGE_SIZE, target_count - len(posts))
        response = requests.get(
            NAVER_BLOG_SEARCH_URL,
            headers=naver_open_api_headers,
            params={"query": keyword, "display": display, "start": start, "sort": "sim"},
            timeout=15,
        )
        response.raise_for_status()
        items = response.json().get("items", [])

        for item in items:
            title = _strip_tags(item.get("title", ""))
            contents = _strip_tags(item.get("description", ""))
            posts.append({"title": title, "contents": contents, "url": item.get("link", "")})

        if len(items) < display:
            break
        start += display

    return posts


def naver_local_search(query, display=5):
    """네이버 지역검색 공식 API로 실제 등록된 업체 후보를 조회합니다
    (블로그 상호명 검증용 — 카카오맵 검증이 실패했을 때 이름을 다시 맞춰보는 용도)."""
    response = requests.get(
        NAVER_LOCAL_SEARCH_URL,
        headers=naver_open_api_headers,
        params={"query": query, "display": display, "sort": "random"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    return [
        {
            "title": _strip_tags(item.get("title", "")),
            "category": item.get("category", ""),
            "road_address": item.get("roadAddress", ""),
            "address": item.get("address", ""),
        }
        for item in data.get("items", [])
    ]
