"""Google Programmable Search JSON API 래퍼."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


@dataclass
class SearchHit:
    url: str
    title: str
    snippet: str
    query: str
    country: str
    category: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call(params: dict) -> dict:
    resp = requests.get(SEARCH_ENDPOINT, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def search(
    api_key: str,
    cse_id: str,
    query: str,
    country: str,
    category: str,
    num_results: int = 10,
    language: str | None = None,
) -> list[SearchHit]:
    """단일 쿼리 검색. API 한 번에 최대 10건이라 페이지네이션으로 채운다."""
    hits: list[SearchHit] = []
    start = 1
    while len(hits) < num_results and start <= 91:
        page_size = min(10, num_results - len(hits))
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": page_size,
            "start": start,
        }
        if language:
            params["lr"] = language
        try:
            data = _call(params)
        except Exception as exc:  # noqa: BLE001
            logger.warning("검색 실패 (query=%r): %s", query, exc)
            break

        items = data.get("items", [])
        if not items:
            break
        for item in items:
            hits.append(
                SearchHit(
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    query=query,
                    country=country,
                    category=category,
                )
            )
        start += page_size
    return hits
