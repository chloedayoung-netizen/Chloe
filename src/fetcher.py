"""URL HTML 수집 및 본문 텍스트 추출.

접근 불가/로그인 필요/에러 페이지/차단 도메인은 건너뛴다.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 이메일 정규식 (HTML 원문에서 직접 추출)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# 이메일로 오인되기 쉬운 잡음(이미지/코드 파일, 추적 도메인, 예시 주소 등)을 걸러낸다.
_EMAIL_JUNK = (
    # 이미지/코드/폰트 등 자산 파일명이 user@file.ext 형태로 잡히는 경우
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".mp4",
    ".css", ".js", ".json", ".map", ".scss", ".less", ".woff", ".ttf",
    ".min", "@2x", "@3x",
    # 추적/플랫폼 도메인
    "sentry.io", "wixpress.com", "@sentry",
    # 예시/플레이스홀더 주소
    "example.com", "example.org", "example@", "@example",
    "yourdomain", "@domain.", "domain.com", "email.com", "@email.",
    "xxx@", "@xxx", "your@", "youremail", "yourname", "test@test",
    "sample@", "user@domain", "@sample",
)

# 인스타그램 핸들 추출 (instagram.com/<handle>)
_INSTA_RE = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")
# 핸들이 아닌 경로(게시물/탐색 등)는 제외한다.
_INSTA_SKIP = {
    "p", "explore", "accounts", "reel", "reels", "stories",
    "tv", "about", "developer", "legal", "directory", "web", "",
}

# 연락처 페이지로 추정되는 링크 텍스트/경로 키워드
_CONTACT_HINTS = ("contact", "about", "wholesale", "stockist", "trade", "press", "kontakt")

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
    html: str = ""  # 연락처 추출용 원본 HTML (성공 시에만 채움)


@dataclass
class Contacts:
    emails: list[str] = field(default_factory=list)
    instagram: list[str] = field(default_factory=list)


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

    return FetchResult(url, True, text=text, html=resp.text)


# --------------------------------------------------------------------------
# 연락처(이메일·인스타) 수집 — 발굴된 페이지에서 무료로 추출.
# 메인 페이지에 이메일이 없으면 contact/about 페이지 한 곳만 더 들어가 본다.
# --------------------------------------------------------------------------
def find_emails(html: str) -> list[str]:
    """HTML 원문에서 이메일을 추출(잡음 제거, 중복 제거, 소문자화)."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in _EMAIL_RE.findall(html or ""):
        email = raw.strip().rstrip(".").lower()
        if email in seen:
            continue
        if any(junk in email for junk in _EMAIL_JUNK):
            continue
        seen.add(email)
        out.append(email)
    return out


def find_instagram(html: str) -> list[str]:
    """HTML 원문에서 인스타그램 핸들(@handle)을 추출."""
    out: list[str] = []
    seen: set[str] = set()
    for handle in _INSTA_RE.findall(html or ""):
        h = handle.strip().strip(".").lower()
        if not h or h in _INSTA_SKIP or h in seen:
            continue
        seen.add(h)
        out.append("@" + h)
    return out


def _find_contact_links(html: str, base_url: str) -> list[str]:
    """같은 도메인 안에서 contact/about/wholesale 등으로 보이는 링크를 모은다."""
    soup = BeautifulSoup(html or "", "lxml")
    base_host = (urlparse(base_url).hostname or "").lower()
    found: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True).lower()
        haystack = (href + " " + text).lower()
        if not any(hint in haystack for hint in _CONTACT_HINTS):
            continue
        full = urljoin(base_url, href)
        if (urlparse(full).hostname or "").lower() != base_host:
            continue
        if full in seen:
            continue
        seen.add(full)
        found.append(full)
    return found


def _raw_get(url: str, *, timeout: int, user_agent: str) -> str:
    """단순 GET 으로 HTML 문자열을 반환(실패하면 빈 문자열)."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": user_agent, "Accept-Language": "en-US,en;q=0.9"},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return ""
    if resp.status_code >= 400:
        return ""
    if "html" not in resp.headers.get("Content-Type", "").lower():
        return ""
    return resp.text


def collect_contacts(
    page_url: str,
    html: str,
    *,
    timeout: int = 15,
    user_agent: str = "Mozilla/5.0",
    follow_contact_page: bool = True,
) -> Contacts:
    """발굴된 페이지에서 연락처를 추출. 이메일이 없으면 contact 페이지 1곳을 더 본다."""
    emails = find_emails(html)
    instagram = find_instagram(html)

    if follow_contact_page and not emails:
        for link in _find_contact_links(html, page_url)[:2]:
            sub_html = _raw_get(link, timeout=timeout, user_agent=user_agent)
            if not sub_html:
                continue
            emails = find_emails(sub_html)
            if not instagram:
                instagram = find_instagram(sub_html)
            if emails:
                break

    return Contacts(emails=emails, instagram=instagram)
