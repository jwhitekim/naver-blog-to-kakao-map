import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from blog_place_collector.clients.kakao_session import load_cookie_header

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
EXAMPLE_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.example.yaml"

load_dotenv(PROJECT_ROOT / ".env")

_resolved_settings_path = (
    SETTINGS_PATH if SETTINGS_PATH.exists() else EXAMPLE_SETTINGS_PATH
)
with _resolved_settings_path.open(encoding="utf-8") as f:
    _settings = yaml.safe_load(f)

_search_settings = _settings["search"]

MAX_PAGES = _search_settings["max_pages"]
TOP_N = _search_settings["top_n"]
KEYWORD = _search_settings["keyword"]
AREA_KEYWORD = KEYWORD.split()[0]
KAKAO_SEARCH_RADIUS = _search_settings["kakao_search_radius"]

NAVER_BLOG_API_URL = _settings["naver"]["api_url"]

params = {
    "countPerPage": "7",
    "currentPage": "1",
    "endDate": "",
    "keyword": KEYWORD,
    "orderBy": "sim",
    "startDate": "",
    "type": "post",
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_LOCAL_SEARCH_URL = _settings["kakao"]["local_search_url"]
KAKAO_TRANSCOORD_URL = _settings["kakao"]["transcoord_url"]
KAKAO_FAVORITE_ADD_URL = _settings["kakao"]["favorite_add_url"]


def kakao_map_headers():
    return {
        **_settings["kakao"]["map_headers"],
        "cookie": load_cookie_header(),
    }


kakao_auth_headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

headers = _settings["naver"]["headers"]


def credential_status():
    """비밀값을 노출하지 않고 로컬 설정 준비 상태만 반환합니다."""
    return {
        "gemini": bool(GEMINI_API_KEY),
        "kakao_rest": bool(KAKAO_REST_API_KEY),
        "kakao_cookie": bool(load_cookie_header()),
        "settings": SETTINGS_PATH.exists(),
    }
