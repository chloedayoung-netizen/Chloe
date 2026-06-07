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
    openai_api_key: str
    openai_model: str
    service_account_file: str
    sheet_id: str
    sheet_tab: str

    @classmethod
    def load(cls) -> "Env":
        load_dotenv()
        missing = []

        def req(key: str) -> str:
            val = os.getenv(key, "").strip()
            if not val:
                missing.append(key)
            return val

        env = cls(
            google_api_key=req("GOOGLE_API_KEY"),
            google_cse_id=req("GOOGLE_CSE_ID"),
            openai_api_key=req("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06").strip(),
            service_account_file=req("GOOGLE_SERVICE_ACCOUNT_FILE"),
            sheet_id=req("GOOGLE_SHEET_ID"),
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
