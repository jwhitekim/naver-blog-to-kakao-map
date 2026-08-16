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
cp backend/.env.example backend/.env
cp backend/config/settings.example.yaml backend/config/settings.yaml
```

`backend/.env`에 API 키를 입력하고, `backend/config/settings.yaml`의 예제
URL을 실제 엔드포인트로 변경합니다. 이 저장소에 실제 설정 파일이 이미 있다면
복사 단계는 건너뛰세요.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm install && cd ..
.venv/bin/python backend/main.py
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. FastAPI 문서는
<http://127.0.0.1:8000/docs>에서 확인할 수 있습니다.

`python backend/main.py`는 Svelte 소스가 변경되었거나 빌드 파일이 없으면 자동으로
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
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v  # 백엔드 테스트
cd frontend && npm run build   # 프론트엔드 프로덕션 빌드
.venv/bin/python backend/main.py --reload  # 통합 서버 + 백엔드 자동 새로고침
cd frontend && npm run dev     # Svelte 개발 서버만 별도로 실행할 때 사용
```

## CI/CD

`main` 브랜치에 push 또는 PR이 열리면 GitHub Actions(`.github/workflows/ci-cd.yml`)가
백엔드 테스트, 프론트엔드 빌드, Docker 이미지 빌드를 검증합니다. 세 검증이 모두
통과하고 `main`에 직접 push된 경우에만 OpenSSH로 배포 서버(Windows + WSL)에 접속해
`wsl.exe -- bash`로 WSL 안에 들어간 뒤 최신 코드를 받고
`docker compose up -d --build`를 실행합니다.

배포를 사용하려면 저장소 Settings → Secrets and variables → Actions에 아래 값을
등록하세요 (Settings → Environments에 `production` 환경을 만들어 등록해도 됩니다).

| Secret | 설명 |
| --- | --- |
| `SSH_PRIVATE_KEY` | 배포 서버 접속용 개인키 (OpenSSH 형식) |
| `SSH_HOST` (또는 `SERVER_HOST`) | 배포 서버 호스트/IP |
| `SSH_PORT` | 배포 서버 SSH 포트 |
| `SSH_USER` (또는 `SERVER_USER`) | 배포 서버 SSH 사용자 |

배포 경로는 워크플로우에 `/mnt/c/Users/admin/joonspace/naver-blog-to-kakao-map`으로
고정되어 있습니다. 경로가
바뀌면 `.github/workflows/ci-cd.yml`의 `Deploy` 스텝을 직접 수정하세요. 이 WSL 경로에
저장소가 이미 `git clone`되어 있어야 하고, `git`, `docker`, `docker compose` 플러그인이
WSL 안에 설치되어 있어야 합니다 (최초 1회는 수동으로 `git clone` 후
`setup-nginx-https.sh`로 초기 설정하세요).

## 더 읽어보기

- [docs/decisions.md](docs/decisions.md) — 상호명 추출·지역/반경 처리·매칭 로직을
  왜 지금 방식으로 짰는지, 어떤 대안을 검토하고 기각했는지 기록한 설계 노트.
