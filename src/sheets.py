"""Google Sheets append + URL 중복 방지."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Sheet 컬럼 순서 (README 의 컬럼 설계와 일치)
HEADERS = [
    "source_url",       # A  근거 URL (중복 판정 키)
    "company_name",     # B
    "country",          # C
    "category",         # D
    "stocked_brands",   # E  입점 브랜드 (콤마 구분)
    "recent_signal",    # F  최근 신호
    "evidence_text",    # G  근거 문장 (필수)
    "personalized_opener",  # H 개인화 메일 첫 문장
    "is_relevant_buyer",    # I
    "confidence",       # J
    "status",           # K  new / reviewed / contacted / replied
    "search_query",     # L
    "created_at",       # M  UTC ISO8601
]

STATUS_NEW = "new"


class SheetClient:
    def __init__(self, service_account_file: str, sheet_id: str, tab: str):
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        self._svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self.sheet_id = sheet_id
        self.tab = tab

    # ---- 초기화 / 헤더 ----
    def ensure_header(self) -> None:
        """첫 행에 헤더가 없으면 기록한다."""
        rng = f"{self.tab}!A1:{_col(len(HEADERS))}1"
        result = (
            self._svc.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=rng)
            .execute()
        )
        values = result.get("values", [])
        if not values or values[0] != HEADERS:
            self._svc.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=rng,
                valueInputOption="RAW",
                body={"values": [HEADERS]},
            ).execute()
            logger.info("헤더 행을 작성했습니다.")

    # ---- 중복 방지 ----
    def existing_urls(self) -> set[str]:
        """이미 저장된 source_url(A열) 집합을 반환."""
        rng = f"{self.tab}!A2:A"
        result = (
            self._svc.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=rng)
            .execute()
        )
        rows = result.get("values", [])
        return {row[0].strip() for row in rows if row and row[0].strip()}

    # ---- append ----
    def append_row(self, record: dict, *, search_query: str = "") -> None:
        row = _record_to_row(record, search_query=search_query)
        self._svc.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range=f"{self.tab}!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()


def _record_to_row(record: dict, *, search_query: str = "") -> list:
    brands = record.get("stocked_brands", [])
    if isinstance(brands, list):
        brands = ", ".join(brands)
    return [
        record.get("source_url", ""),
        record.get("company_name", ""),
        record.get("country", ""),
        record.get("category", ""),
        brands,
        record.get("recent_signal", ""),
        record.get("evidence_text", ""),
        record.get("personalized_opener", ""),
        str(record.get("is_relevant_buyer", "")),
        record.get("confidence", ""),
        record.get("status", STATUS_NEW),
        search_query,
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
    ]


def _col(n: int) -> str:
    """1-indexed 컬럼 번호 → A1 표기 문자 (1->A, 27->AA)."""
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s
