import json
from collections import Counter

import requests

from blog_place_collector.config import GEMINI_API_KEY, GEMINI_API_URL

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
각 항목에서 리뷰 대상으로 언급된 가게, 시설, 업체의 상호명을 추출하세요.

규칙:
- 상호명은 카카오맵에서 검색할 수 있는 정식 명칭으로 통일하세요.
- 지점명이 명확히 언급되면 지점명까지 포함하세요.
- 검색 지역명(예: 강남, 이태원)은 실제 지점명의 일부일 때만 포함하고, 단순히 위치를 설명하는 수식어라면 제외하세요.
- 같은 가게가 여러 항목에서 다른 표기로 언급되더라도 동일한 상호명 하나로 통일해서 출력하세요.
- 제목에 없어도 본문에 구체적인 상호명이 있으면 추출하세요.
- 지역명, 역 이름, 업종 같은 일반 단어만 있고 구체적인 상호명이 없으면 제외하세요.
- 리뷰 대상이 아닌 장소나 상호명이 불분명한 항목은 제외하세요.

목록:
{items}
"""


def _build_prompt(posts):
    numbered = "\n".join(
        f"{i}. 제목: {post['title']}\n   본문: {post['contents']}"
        for i, post in enumerate(posts, start=1)
    )
    return PROMPT_TEMPLATE.format(items=numbered)


def extract_business_names(posts):
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


def top_business_names(posts, top_n=5):
    results = extract_business_names(posts)
    counter = Counter(result["name"] for result in results)
    return counter.most_common(top_n)


def top_business_candidates(posts, top_n=5):
    """언급 횟수와 근거 포스트를 함께 묶어 UI용 후보를 만듭니다."""
    results = extract_business_names(posts)
    counter = Counter(result["name"] for result in results)
    posts_by_name = {}
    for result in results:
        source = result["post"]
        sources = posts_by_name.setdefault(result["name"], [])
        if not any(item["url"] == source["url"] for item in sources):
            sources.append(
                {
                    "title": source["title"],
                    "url": source["url"],
                }
            )

    return [
        {
            "name": name,
            "mention_count": count,
            "sources": posts_by_name.get(name, []),
        }
        for name, count in counter.most_common(top_n)
    ]
