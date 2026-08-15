import json
from collections import Counter

import requests

from blog_place_collector.config import GEMINI_API_KEY, GEMINI_API_URL

REGIONS_SCHEMA = {
    "type": "ARRAY",
    "items": {"type": "STRING"},
}

REGIONS_PROMPT_TEMPLATE = """\
아래 검색어 문자열 자체에서만 지역명을 전부 추출하세요 (구/동/역/골목상권 이름 등,
예: 강남, 성수동, 신논현역, 송리단길). 검색어 안에서만 찾고, 다른 지식이나 추측은
쓰지 마세요. 지역명이 전혀 없으면 빈 배열을 반환하세요.

검색어: "{keyword}"
"""

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
사용자가 검색한 키워드는 "{keyword}"입니다.
아래는 이 키워드로 찾은 네이버 블로그 검색 결과 목록입니다 (제목 + 본문 일부).
각 항목에서 리뷰 대상으로 언급된 가게, 시설, 업체의 상호명을 추출하세요.

규칙:
- 검색 키워드가 나타내는 장소 유형·주제와 실제로 관련된 상호명만 추출하세요.
  글이 여러 장소를 나열하는 목록형/추천형 글이더라도, 키워드와 무관한 업종·시설은 제외하세요.
  (예: "영화관"을 검색했는데 글이 "실내 놀거리 15선"이라 아쿠아리움·전시공간도 같이 나열돼 있다면,
  그중 영화관에 해당하는 것만 추출하고 나머지는 제외하세요.)
- 상호명으로 보이거나 상호명으로 추측되는 표현이 있으면 확신이 없어도 최대한 추출하세요.
  실제로 존재하는 상호인지는 이후 카카오맵 검색으로 검증하니, 애매하다고 여기서 걸러내지 마세요.
- 상호명은 카카오맵에서 검색할 수 있는 정식 명칭에 가깝게 통일하세요.
- 지점명이 명확히 언급되면 지점명까지 포함하세요.
- 검색 지역명(예: 강남, 이태원)은 실제 지점명의 일부일 때만 포함하고, 단순히 위치를 설명하는 수식어라면 제외하세요.
- 같은 가게가 여러 항목에서 다른 표기로 언급되더라도 동일한 상호명 하나로 통일해서 출력하세요.
- 제목에 없어도 본문에 구체적인 상호명이 있으면 추출하세요.
- 지역명, 역 이름, 업종처럼 상호명이 전혀 아닌 일반 단어만 있는 경우에만 제외하세요.

목록:
{items}
"""


def _call_gemini(prompt, response_schema):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
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
    return json.loads(text)


def extract_regions(keyword):
    """검색 키워드 문자열 자체에서 지역명을 추출합니다. 블로그 본문은 보지 않고
    키워드만 보므로, 여러 지역이 섞여 있거나 순서가 달라도 안정적으로 동작합니다."""
    regions = _call_gemini(REGIONS_PROMPT_TEMPLATE.format(keyword=keyword), REGIONS_SCHEMA)
    return [region.strip() for region in regions if region.strip()]


def _build_prompt(posts, keyword):
    numbered = "\n".join(
        f"{i}. 제목: {post['title']}\n   본문: {post['contents']}"
        for i, post in enumerate(posts, start=1)
    )
    return PROMPT_TEMPLATE.format(keyword=keyword, items=numbered)


def extract_business_names(posts, keyword):
    entries = _call_gemini(_build_prompt(posts, keyword), RESPONSE_SCHEMA)

    names = []
    for entry in entries:
        index = entry["index"] - 1
        name = entry["name"].strip()
        if 0 <= index < len(posts) and name:
            names.append({"name": name, "post": posts[index]})
    return names


def top_business_names(posts, keyword, top_n=5):
    results = extract_business_names(posts, keyword)
    counter = Counter(result["name"] for result in results)
    return counter.most_common(top_n)
