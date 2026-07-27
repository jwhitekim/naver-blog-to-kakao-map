import os

import yaml
from dotenv import load_dotenv

load_dotenv()

with open("settings.yaml", encoding="utf-8") as f:
    _settings = yaml.safe_load(f)

_search_settings = _settings["search"]

MAX_PAGES = _search_settings["max_pages"]
TOP_N = _search_settings["top_n"]
KEYWORD = _search_settings["keyword"]
AREA_KEYWORD = KEYWORD.split()[0]  # 카카오맵 검색 시 지역을 좁히는 데 쓰는 기준 지명입니다.
KAKAO_SEARCH_RADIUS = _search_settings["kakao_search_radius"]

NAVER_BLOG_API_URL = _settings["naver"]["api_url"]

params = {
    "countPerPage": "7",
    "currentPage": "1",
    "endDate": "",
    "keyword": KEYWORD,  # 검색어를 여기에 넣습니다.
    "orderBy": "sim",
    "startDate": "",
    "type": "post"
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_LOCAL_SEARCH_URL = _settings["kakao"]["local_search_url"]
KAKAO_TRANSCOORD_URL = _settings["kakao"]["transcoord_url"]
KAKAO_FAVORITE_ADD_URL = _settings["kakao"]["favorite_add_url"]

kakao_map_headers = {
    **_settings["kakao"]["map_headers"],
    "cookie": os.getenv("KAKAO_COOKIE"),
}

kakao_auth_headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

headers = _settings["naver"]["headers"]
