# Placepick

네이버 블로그 검색 결과에서 자주 언급된 장소를 AI로 추출하고, 검토한 장소만
카카오맵 즐겨찾기에 추가하는 로컬 웹 애플리케이션입니다.

## 준비 사항

- Python 3.9 이상
- Node.js 20.19 이상
- Gemini API 키
- Kakao REST API 키

## 처음 실행

```bash
cp .env.example .env
cp config/settings.example.yaml config/settings.yaml
```

`.env`에 API 키를 입력하고, `config/settings.yaml`의 예제 URL을 실제
엔드포인트로 변경합니다. 이 저장소에 실제 설정 파일이 이미 있다면 복사 단계는
건너뛰세요.

```bash
make setup
make kakao-login   # 최초 1회, 브라우저 창에서 카카오 로그인
python main.py
```

`make kakao-login`은 로컬 화면에서 브라우저 창을 띄워 카카오맵 로그인(2단계
인증 포함)을 한 번 진행하고, 그 세션을 `.kakao_session/`에 저장합니다. 이후
즐겨찾기 추가 요청은 이 저장된 세션을 재사용하며, 세션이 완전히 만료되면 다시
`make kakao-login`을 실행하면 됩니다. 이 스크립트는 화면이 있는 로컬 환경에서
실행해야 하며, Docker 컨테이너 안에서는 실행할 수 없습니다.

브라우저에서 <http://127.0.0.1:8000>을 엽니다. FastAPI 문서는
<http://127.0.0.1:8000/docs>에서 확인할 수 있습니다.

`python main.py`는 Svelte 소스가 변경되었거나 빌드 파일이 없으면 자동으로
프론트엔드를 빌드합니다. 이후 FastAPI가 API와 프론트엔드 빌드 파일을 모두
`127.0.0.1:8000`에서 제공합니다. 프론트엔드 개발 서버를 따로 실행할 필요가
없습니다.

## 주요 흐름

1. 검색어와 수집 범위를 입력합니다.
2. 네이버 블로그 글에서 Gemini가 상호명을 추출합니다.
3. 카카오 로컬 검색 결과와 매칭된 장소 및 근거 블로그를 검토합니다.
4. 선택한 장소만 카카오맵 즐겨찾기에 추가합니다.

API 키와 카카오 쿠키는 백엔드에서만 사용하며 브라우저 응답에 포함하지 않습니다.

## 명령어

```bash
make test      # 백엔드 테스트
make build     # 프론트엔드 프로덕션 빌드
make dev       # 통합 서버 + 백엔드 자동 새로고침
make frontend  # Svelte 개발 서버만 별도로 실행할 때 사용
python main.py --cli  # 기존 터미널 수집 방식
```
