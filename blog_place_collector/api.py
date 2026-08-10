from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from blog_place_collector.clients.kakao import add_favorite
from blog_place_collector.config import credential_status
from blog_place_collector.service import preview_collection

app = FastAPI(
    title="Placepick API",
    description="네이버 블로그의 장소를 카카오맵 즐겨찾기로 옮기는 로컬 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreviewRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=80)
    max_pages: int = Field(default=10, ge=1, le=30)
    top_n: int = Field(default=10, ge=1, le=20)
    radius: int = Field(default=5000, ge=100, le=20000)


class Place(BaseModel):
    type: str = "place"
    key: int
    display1: str
    display2: str
    x: float
    y: float
    color: str = "02"
    memo: str = ""
    folderid: int = 0
    category: str = ""
    phone: str = ""
    place_url: str = ""


class FavoriteRequest(BaseModel):
    places: List[Place] = Field(min_length=1, max_length=20)


def _friendly_error(error):
    if isinstance(error, requests.Timeout):
        return "외부 서비스 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
    if isinstance(error, requests.HTTPError):
        status = error.response.status_code if error.response is not None else None
        if status in (401, 403):
            return "카카오 로그인이 만료되었습니다. `make kakao-login`을 다시 실행해 주세요."
        if status == 429:
            return "외부 서비스 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."
        return f"외부 서비스 요청에 실패했습니다.{f' (HTTP {status})' if status else ''}"
    if isinstance(error, ValueError):
        return str(error)
    return str(error) or "요청 처리 중 알 수 없는 오류가 발생했습니다."


def _is_auth_expired(error):
    if isinstance(error, requests.HTTPError):
        status = error.response.status_code if error.response is not None else None
        return status in (401, 403)
    return isinstance(error, ValueError)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "credentials": credential_status(),
    }


@app.post("/api/collections/preview")
async def preview(payload: PreviewRequest):
    try:
        result = await run_in_threadpool(
            preview_collection,
            payload.keyword.strip(),
            payload.max_pages,
            payload.top_n,
            payload.radius,
        )
        return {
            "query": payload.keyword.strip(),
            **result,
        }
    except (requests.RequestException, ValueError, KeyError, IndexError) as error:
        raise HTTPException(status_code=502, detail=_friendly_error(error)) from error


@app.post("/api/favorites")
async def create_favorites(payload: FavoriteRequest):
    added = []
    failed = []
    for place in payload.places:
        try:
            await run_in_threadpool(add_favorite, place.model_dump())
            added.append({"key": place.key, "name": place.display1})
        except (requests.RequestException, ValueError) as error:
            failed.append(
                {
                    "key": place.key,
                    "name": place.display1,
                    "message": _friendly_error(error),
                    "auth_expired": _is_auth_expired(error),
                }
            )

    return {"added": added, "failed": failed}


# API 라우트를 먼저 등록한 뒤 Svelte 빌드 결과를 루트 경로에서 제공합니다.
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dist), html=True),
        name="frontend",
    )
