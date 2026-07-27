import json
from collections import Counter

import requests

from config import GEMINI_API_KEY, GEMINI_API_URL

RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "index": {"type": "INTEGER"},
            "name": {"type": "STRING"},
        },
        "required": ["index", "name"],
    },
}

PROMPT_TEMPLATE = """\
아래는 네이버 블로그 검색 결과 목록입니다 (제목 + 본문 일부).
각 항목에서 언급된 카페/베이커리 등 특정 업체의 상호명을 추출하세요.

규칙:
- 상호명은 정식 브랜드명으로 통일하세요 (예: "온더브레드 복정점", "온더브레드복정" -> "온더브레드").
- 제목에 없어도 본문에 구체적인 상호명이 있으면 추출하세요.
- 지역명, 역 이름, 맛집/카페 같은 일반 단어만 있고 구체적인 상호명이 없으면 그 항목은 결과에서 제외하세요.
- 상호명이 없는 항목(예: 주차장 안내, 교회 등 카페와 무관한 내용)은 제외하세요.

목록:
{items}
"""


def _build_prompt(posts):
    numbered = "\n".join(
        f"{i}. 제목: {post['title']}\n   본문: {post['contents']}"
        for i, post in enumerate(posts, start=1)
    )
    return PROMPT_TEMPLATE.format(items=numbered)


def extract_cafe_names(posts):
    payload = {
        "contents": [{"parts": [{"text": _build_prompt(posts)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    response = requests.post(
        GEMINI_API_URL,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    entries = json.loads(text)

    names = []
    for entry in entries:
        index = entry["index"] - 1
        name = entry["name"].strip()
        if 0 <= index < len(posts) and name:
            names.append({"name": name, "post": posts[index]})
    return names


def top_cafe_names(posts, top_n=5):
    results = extract_cafe_names(posts)
    counter = Counter(r["name"] for r in results)
    return counter.most_common(top_n)
