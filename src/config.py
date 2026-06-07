"""환경변수(.env)와 config.yaml 로딩."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from itertools import product
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class Env:
    """.env 에서 읽는 비밀/연결 정보."""

    google_api_key: str
    google_cse_id: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    service_account_file: str
    sheet_id: str
    sheet_tab: str

    @classmethod
    def load(cls, require_sheets: bool = True) -> "Env":
        """환경변수를 로딩한다.

        require_sheets=False 이면 Google Sheets 관련 자격증명을 필수로 보지
        않는다. (예: --dry-run 모드에서는 검색/LLM 키만 있어도 동작)

        LLM 은 OpenAI 호환 API(기본값: OpenRouter)를 사용한다.
        """
        load_dotenv()
        missing = []

        def req(key: str, required: bool = True) -> str:
            val = os.getenv(key, "").strip()
            if not val and required:
                missing.append(key)
            return val

        env = cls(
            google_api_key=req("GOOGLE_API_KEY"),
            google_cse_id=req("GOOGLE_CSE_ID"),
            llm_api_key=req("OPENROUTER_API_KEY"),
            llm_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ).strip(),
            llm_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-2024-08-06").strip(),
            service_account_file=req("GOOGLE_SERVICE_ACCOUNT_FILE", require_sheets),
            sheet_id=req("GOOGLE_SHEET_ID", require_sheets),
            sheet_tab=os.getenv("GOOGLE_SHEET_TAB", "buyers").strip(),
        )
        if missing:
            raise SystemExit(
                "필수 환경변수가 설정되지 않았습니다: "
                + ", ".join(missing)
                + "\n.env.example 을 참고해 .env 를 작성하세요."
            )
        return env


@dataclass
class Config:
    """config.yaml 내용."""

    queries: list[str]
    countries: list[str]
    categories: list[str]
    search: dict[str, Any] = field(default_factory=dict)
    fetch: dict[str, Any] = field(default_factory=dict)
    extract: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            queries=data.get("queries", []),
            countries=data.get("countries", []),
            categories=data.get("categories", []),
            search=data.get("search", {}),
            fetch=data.get("fetch", {}),
            extract=data.get("extract", {}),
        )

    def expanded_queries(self) -> list[tuple[str, str, str]]:
        """(query_text, country, category) 조합을 생성.

        {country}/{category} 플레이스홀더가 없는 쿼리도 안전하게 처리한다.
        """
        combos: list[tuple[str, str, str]] = []
        countries = self.countries or [""]
        categories = self.categories or [""]
        for q, country, category in product(self.queries, countries, categories):
            text = q.format(country=country, category=category).strip()
            combos.append((text, country, category))
        # 중복 쿼리 제거 (플레이스홀더 없는 경우 동일 텍스트가 반복될 수 있음)
        seen: set[str] = set()
        unique: list[tuple[str, str, str]] = []
        for item in combos:
            if item[0] not in seen:
                seen.add(item[0])
                unique.append(item)
        return unique
