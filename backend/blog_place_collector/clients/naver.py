import json

import requests

from blog_place_collector.config import (
    KEYWORD,
    MAX_PAGES,
    NAVER_BLOG_API_URL,
    headers,
    params,
)


def _strip_highlight(text):
    return text.replace('<strong class="search_keyword">', "").replace("</strong>", "")


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
