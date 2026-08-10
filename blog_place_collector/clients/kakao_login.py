"""카카오맵 로그인 세션을 저장하는 1회성 스크립트.

Docker 컨테이너 안이 아니라, 화면이 있는 로컬 환경에서 직접 실행하세요.
    python -m blog_place_collector.clients.kakao_login
"""

from playwright.sync_api import sync_playwright

from blog_place_collector.clients.kakao_session import SESSION_DIR, STATE_PATH


def login():
    SESSION_DIR.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://map.kakao.com")
        input("브라우저에서 카카오 로그인을 완료한 뒤, 여기로 돌아와 Enter를 눌러주세요...")
        context.storage_state(path=str(STATE_PATH))
        browser.close()
    print(f"세션을 저장했습니다: {STATE_PATH}")


if __name__ == "__main__":
    login()
