import requests

from config import KAKAO_FAVORITE_ADD_URL, kakao_map_headers


def add_favorite(place):
    payload = {"datas": [place]}
    response = requests.post(
        KAKAO_FAVORITE_ADD_URL,
        headers=kakao_map_headers,
        json=payload,
        timeout=10,
    )
    print(f"Status Code: {response.status_code}")
    print(response.text)
    return response
