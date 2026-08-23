import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

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

TARGET_COUNT = _search_settings["target_count"]
TOP_N = _search_settings["top_n"]
KEYWORD = _search_settings["keyword"]
AREA_KEYWORD = KEYWORD.split()[0] if KEYWORD.split() else ""
KAKAO_SEARCH_RADIUS = _search_settings["kakao_search_radius"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_LOCAL_SEARCH_URL = _settings["kakao"]["local_search_url"]
kakao_auth_headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_LOCAL_SEARCH_URL = "https://openapi.naver.com/v1/search/local.json"
NAVER_BLOG_SEARCH_URL = "https://openapi.naver.com/v1/search/blog.json"
naver_open_api_headers = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID or "",
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET or "",
}


def credential_status():
    """비밀값을 노출하지 않고 로컬 설정 준비 상태만 반환합니다."""
    return {
        "gemini": bool(GEMINI_API_KEY),
        "kakao_rest": bool(KAKAO_REST_API_KEY),
        "naver_local": bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET),
        "settings": SETTINGS_PATH.exists(),
    }
