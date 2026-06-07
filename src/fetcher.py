"""URL HTML 수집 및 본문 텍스트 추출.

접근 불가/로그인 필요/에러 페이지/차단 도메인은 건너뛴다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 로그인/차단 페이지를 암시하는 신호
LOGIN_MARKERS = (
    "sign in",
    "log in",
    "login",
    "create an account",
    "enable javascript",
    "access denied",
    "are you a robot",
    "captcha",
    "cloudflare",
    "attention required",
)


@dataclass
class FetchResult:
    url: str
    ok: bool
    text: str = ""
    reason: str = ""


def is_blocked_domain(url: str, blocked: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in blocked)


def _clean_text(html: str, max_chars: int) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # 공백 정규화
    text = " ".join(text.split())
    return text[:max_chars]


def fetch(
    url: str,
    *,
    timeout: int = 15,
    max_content_chars: int = 12000,
    user_agent: str = "Mozilla/5.0",
    blocked_domains: list[str] | None = None,
) -> FetchResult:
    blocked_domains = blocked_domains or []
    if is_blocked_domain(url, blocked_domains):
        return FetchResult(url, False, reason="blocked_domain")

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True
        )
    except requests.RequestException as exc:
        return FetchResult(url, False, reason=f"request_error: {exc.__class__.__name__}")

    if resp.status_code in (401, 403):
        return FetchResult(url, False, reason=f"auth_required ({resp.status_code})")
    if resp.status_code >= 400:
        return FetchResult(url, False, reason=f"http_error ({resp.status_code})")

    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        return FetchResult(url, False, reason=f"non_html ({content_type})")

    text = _clean_text(resp.text, max_content_chars)
    if len(text) < 200:
        return FetchResult(url, False, reason="too_little_text")

    lowered = text[:1500].lower()
    if any(marker in lowered for marker in LOGIN_MARKERS):
        return FetchResult(url, False, reason="login_or_block_page")

    return FetchResult(url, True, text=text)
