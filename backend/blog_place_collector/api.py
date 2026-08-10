from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from blog_place_collector.config import credential_status
from blog_place_collector.service import preview_collection

app = FastAPI(
    title="Placepick API",
    description="네이버 블로그에서 자주 언급된 장소를 찾아 정보를 보여주는 로컬 API",
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


def _friendly_error(error):
    if isinstance(error, requests.Timeout):
        return "외부 서비스 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
    if isinstance(error, requests.HTTPError):
        status = error.response.status_code if error.response is not None else None
        if status in (401, 403):
            return "API 인증 정보가 만료되었거나 올바르지 않습니다."
        if status == 429:
            return "외부 서비스 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."
        return f"외부 서비스 요청에 실패했습니다.{f' (HTTP {status})' if status else ''}"
    if isinstance(error, ValueError):
        return str(error)
    return str(error) or "요청 처리 중 알 수 없는 오류가 발생했습니다."


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


# API 라우트를 먼저 등록한 뒤 Svelte 빌드 결과를 루트 경로에서 제공합니다.
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dist), html=True),
        name="frontend",
    )
