import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_DIR = PROJECT_ROOT / ".kakao_session"
STATE_PATH = SESSION_DIR / "state.json"


def load_cookie_header():
    """저장된 카카오맵 로그인 세션에서 쿠키 헤더 문자열을 만듭니다."""
    if not STATE_PATH.exists():
        return None

    with STATE_PATH.open(encoding="utf-8") as f:
        state = json.load(f)

    cookies = [
        cookie
        for cookie in state.get("cookies", [])
        if "kakao.com" in cookie.get("domain", "")
    ]
    if not cookies:
        return None

    return "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in cookies)
