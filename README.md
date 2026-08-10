# Placepick

네이버 블로그 검색 결과에서 자주 언급된 장소를 AI로 추출하고, 카카오맵·네이버지도
링크로 바로 연결해주는 로컬 웹 애플리케이션입니다.

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
python main.py
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. FastAPI 문서는
<http://127.0.0.1:8000/docs>에서 확인할 수 있습니다.

`python main.py`는 Svelte 소스가 변경되었거나 빌드 파일이 없으면 자동으로
프론트엔드를 빌드합니다. 이후 FastAPI가 API와 프론트엔드 빌드 파일을 모두
`127.0.0.1:8000`에서 제공합니다. 프론트엔드 개발 서버를 따로 실행할 필요가
없습니다.

## 주요 흐름

1. 검색어와 수집 범위를 입력합니다.
2. 네이버 블로그 글에서 Gemini가 상호명을 추출합니다.
3. 카카오 로컬 검색으로 좌표·주소를 매칭합니다.
4. 마음에 드는 장소는 카카오맵/네이버지도 링크로 이동해 영업시간·메뉴·사진을
   확인하고 직접 즐겨찾기합니다.

API 키는 백엔드에서만 사용하며 브라우저 응답에 포함하지 않습니다.

## 명령어

```bash
make test      # 백엔드 테스트
make build     # 프론트엔드 프로덕션 빌드
make dev       # 통합 서버 + 백엔드 자동 새로고침
make frontend  # Svelte 개발 서버만 별도로 실행할 때 사용
```
