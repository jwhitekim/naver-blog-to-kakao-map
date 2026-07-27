import json

import requests

from blog_place_collector.config import (
    MAX_PAGES,
    NAVER_BLOG_API_URL,
    headers,
    params,
)


def _strip_highlight(text):
    return text.replace('<strong class="search_keyword">', "").replace("</strong>", "")


def naver_blog_search():
    posts = []

    try:
        for page in range(1, MAX_PAGES + 1):
            params["currentPage"] = str(page)

            response = requests.get(
                NAVER_BLOG_API_URL,
                headers=headers,
                params=params,
            )
            print(f"Status Code: {response.status_code}")

            # 네이버 응답의 JSON 하이재킹 방지용 접두사를 제거합니다.
            json_text = response.text.split("\n", 1)[1]
            data = json.loads(json_text)

            for post in data["result"]["searchList"]:
                title = _strip_highlight(post["title"])
                contents = _strip_highlight(post["contents"])
                blog_link = post["postUrl"]
                posts.append(
                    {"title": title, "contents": contents, "url": blog_link}
                )
                print(f"{title}\n{blog_link}\n")
        return posts

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
