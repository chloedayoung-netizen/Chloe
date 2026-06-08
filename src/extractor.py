"""OpenAI Structured Outputs 를 사용한 바이어 정보 추출."""
from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .schema import BUYER_SCHEMA

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a B2B export sales researcher. From the given web page text of a "
    "potential overseas retail buyer, extract structured information. "
    "Only use facts present in the page text. Do NOT invent brands, signals, "
    "or quotes. The evidence_text MUST be a verbatim sentence copied from the "
    "page text. A real buyer is a store/retailer/boutique/concept store that "
    "could stock and sell our products. Set is_relevant_buyer to FALSE for "
    "anything that is NOT itself a store, including: news articles, magazines, "
    "press releases, blog posts, reviews, marketplaces or wholesale platforms "
    "(Amazon, Etsy, Faire, Ankorstore, etc.), brand-listing or directory pages, "
    "social media, wikis, and forums. "
    "The personalized_opener must be a single natural English sentence that "
    "references something specific about this buyer."
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_openai(client: OpenAI, model: str, messages: list, temperature: float) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        response_format={"type": "json_schema", "json_schema": BUYER_SCHEMA},
    )
    return resp.choices[0].message.content or ""


def extract(
    client: OpenAI,
    model: str,
    page_text: str,
    *,
    source_url: str,
    country_hint: str = "",
    category_hint: str = "",
    our_brand_context: str = "",
    temperature: float = 0.0,
) -> dict[str, Any] | None:
    """페이지 텍스트에서 구조화된 바이어 정보를 추출.

    실패하거나 스키마 검증에 실패하면 None 반환.
    """
    user_content = (
        f"OUR BRAND CONTEXT:\n{our_brand_context}\n\n"
        f"SEARCH HINTS — country: {country_hint or 'unknown'}, "
        f"category: {category_hint or 'unknown'}\n"
        f"SOURCE URL: {source_url}\n\n"
        f"PAGE TEXT:\n{page_text}"
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    try:
        raw = _call_openai(client, model, messages, temperature)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI 추출 실패 (%s): %s", source_url, exc)
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSON 파싱 실패 (%s): %s", source_url, exc)
        return None

    if not _validate(data, source_url):
        return None
    return data


def _validate(data: dict[str, Any], source_url: str) -> bool:
    """스키마 핵심 제약 검증. evidence_text 는 반드시 존재해야 한다."""
    required_str = [
        "company_name",
        "country",
        "category",
        "recent_signal",
        "evidence_text",
        "personalized_opener",
    ]
    for key in required_str:
        if key not in data or not isinstance(data[key], str):
            logger.warning("필드 누락/형식오류 '%s' (%s)", key, source_url)
            return False
    if not isinstance(data.get("stocked_brands"), list):
        return False
    if not isinstance(data.get("is_relevant_buyer"), bool):
        return False
    # 요구사항 8: evidence_text 는 반드시 포함되어야 한다.
    if not data["evidence_text"].strip():
        logger.info("evidence_text 비어있음 → 스킵 (%s)", source_url)
        return False
    return True
