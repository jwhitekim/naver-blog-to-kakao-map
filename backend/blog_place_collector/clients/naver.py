import html
import json
import re

import requests

from blog_place_collector.config import (
    KEYWORD,
    MAX_PAGES,
    NAVER_BLOG_API_URL,
    NAVER_LOCAL_SEARCH_URL,
    headers,
    naver_open_api_headers,
    params,
)


def _strip_highlight(text):
    text = text.replace('<strong class="search_keyword">', "").replace("</strong>", "")
    return html.unescape(text)


def _strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def naver_blog_search(keyword=KEYWORD, max_pages=MAX_PAGES):
    posts = []
    request_params = {
        **params,
        "keyword": keyword,
    }

    for page in range(1, max_pages + 1):
        request_params["currentPage"] = str(page)

        response = requests.get(
            NAVER_BLOG_API_URL,
            headers=headers,
            params=request_params,
            timeout=15,
        )
        response.raise_for_status()

        # 네이버 응답의 JSON 하이재킹 방지용 접두사를 제거합니다.
        json_text = response.text
        if not json_text.lstrip().startswith("{"):
            parts = json_text.split("\n", 1)
            if len(parts) != 2:
                raise ValueError("네이버 블로그 응답 형식을 확인할 수 없습니다.")
            json_text = parts[1]
        data = json.loads(json_text)

        search_list = data.get("result", {}).get("searchList", [])
        for post in search_list:
            title = _strip_highlight(post.get("title", ""))
            contents = _strip_highlight(post.get("contents", ""))
            blog_link = post.get("postUrl", "")
            posts.append({"title": title, "contents": contents, "url": blog_link})

        if not search_list:
            break

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
