"""Serper.dev (Google 검색 결과) API 래퍼.

Google Programmable Search 의 무료 전체 웹 검색이 중단됨에 따라, 전체 웹
검색이 가능한 Serper.dev 를 사용한다. (https://serper.dev)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SEARCH_ENDPOINT = "https://google.serper.dev/search"


@dataclass
class SearchHit:
    url: str
    title: str
    snippet: str
    query: str
    country: str
    category: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call(api_key: str, payload: dict) -> dict:
    resp = requests.post(
        SEARCH_ENDPOINT,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def search(
    api_key: str,
    query: str,
    country: str,
    category: str,
    num_results: int = 10,
    gl: str | None = None,
    hl: str | None = None,
) -> list[SearchHit]:
    """단일 쿼리 검색. Serper 는 한 번에 최대 100건까지 반환한다.

    gl: 국가 코드(예: "fr", "jp"), hl: 언어 코드(예: "en"). 선택값.
    """
    payload: dict = {"q": query, "num": min(num_results, 100)}
    if gl:
        payload["gl"] = gl
    if hl:
        payload["hl"] = hl

    try:
        data = _call(api_key, payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("검색 실패 (query=%r): %s", query, exc)
        return []

    hits: list[SearchHit] = []
    for item in data.get("organic", [])[:num_results]:
        url = item.get("link", "")
        if not url:
            continue
        hits.append(
            SearchHit(
                url=url,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                query=query,
                country=country,
                category=category,
            )
        )
    return hits
