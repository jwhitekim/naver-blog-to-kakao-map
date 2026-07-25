import json
import requests

from config import MAX_PAGES, NAVER_BLOG_API_URL, headers, params
    

def _strip_highlight(text):
    return text.replace('<strong class="search_keyword">', "").replace("</strong>", "")


def naver_blog_search():
    posts = []

    try:
        for page in range(1, MAX_PAGES + 1):
            params["currentPage"] = str(page)  # 현재 페이지 번호를 업데이트합니다.

            response = requests.get(NAVER_BLOG_API_URL, headers=headers, params=params)
            print(f"Status Code: {response.status_code}")  # 200이면 정상, 403이면 차단, 404면 페이지 없음

            # 네이버는 JSON 하이재킹 방지를 위해 응답 앞에 )]}', 접두사를 붙여서 보냅니다.
            # 이 접두사를 제거해야 정상적인 JSON으로 파싱할 수 있습니다.
            json_text = response.text.split("\n", 1)[1]
            data = json.loads(json_text)

            for post in data["result"]["searchList"]:
                title = _strip_highlight(post["title"])
                contents = _strip_highlight(post["contents"])
                blog_link = post["postUrl"]
                posts.append({"title": title, "contents": contents, "url": blog_link})
                print(f"{title}\n{blog_link}\n")
        return posts

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")