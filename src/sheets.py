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
    "email",            # N  수집된 이메일 (콤마 구분)
    "instagram",        # O  인스타 핸들 (콤마 구분)
]

STATUS_NEW = "new"

# 설정 탭: 사용자가 시트에서 직접 나라/카테고리/검색어를 편집한다.
CONFIG_TAB = "config"

# 설정 탭에서 읽어들이는 키 (A열) → 값은 B열부터 나열
CONFIG_LIST_KEYS = {"countries", "categories", "queries"}
CONFIG_SCALAR_KEYS = {"max_total_urls", "language"}


class SheetClient:
    def __init__(self, service_account_file: str, sheet_id: str, tab: str):
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        self._svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self.sheet_id = sheet_id
        self.tab = tab

    # ---- 탭 존재 보장 ----
    def _existing_tabs(self) -> set[str]:
        meta = self._svc.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        return {s["properties"]["title"] for s in meta.get("sheets", [])}

    def _ensure_tab(self, title: str) -> None:
        if title in self._existing_tabs():
            return
        self._svc.spreadsheets().batchUpdate(
            spreadsheetId=self.sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        ).execute()
        logger.info("탭 '%s' 을(를) 새로 만들었습니다.", title)

    # ---- 초기화 / 헤더 ----
    def ensure_header(self) -> None:
        """결과 탭이 없으면 만들고, 첫 행에 헤더가 없으면 기록한다."""
        self._ensure_tab(self.tab)
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

    # ---- 백필(기존 행 연락처 채우기) ----
    def rows_missing_contacts(self, *, force: bool = False) -> list[dict]:
        """연락처를 채울 대상 행을 반환.

        각 항목: {"row": 행번호(1-indexed), "url": source_url}
        force=False → email/instagram 이 모두 빈 행만.
        force=True  → URL 이 있는 모든 행 (기존 값 갱신/정정용).
        """
        rng = f"{self.tab}!A2:{_col(len(HEADERS))}"
        result = (
            self._svc.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=rng)
            .execute()
        )
        email_idx = HEADERS.index("email")
        insta_idx = HEADERS.index("instagram")
        out: list[dict] = []
        for offset, row in enumerate(result.get("values", [])):
            url = (row[0].strip() if row and row[0] else "")
            if not url:
                continue
            if not force:
                email = row[email_idx].strip() if len(row) > email_idx else ""
                insta = row[insta_idx].strip() if len(row) > insta_idx else ""
                if email or insta:
                    continue  # 이미 연락처 있음 → 건너뜀
            out.append({"row": offset + 2, "url": url})
        return out

    def update_contacts(self, row: int, email: str, instagram: str) -> None:
        """특정 행의 email(N)·instagram(O) 칸만 갱신한다."""
        n_col = _col(HEADERS.index("email") + 1)
        o_col = _col(HEADERS.index("instagram") + 1)
        self._svc.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=f"{self.tab}!{n_col}{row}:{o_col}{row}",
            valueInputOption="RAW",
            body={"values": [[email, instagram]]},
        ).execute()

    # ---- 설정(config) 탭 ----
    def ensure_config_tab(self, defaults: dict) -> None:
        """설정 탭이 없거나 비어 있으면 기본값으로 채워 넣는다.

        defaults: {"countries": [...], "categories": [...], "queries": [...],
                   "max_total_urls": int, "language": str}
        이미 내용이 있으면(사용자가 편집했으면) 건드리지 않는다.
        """
        self._ensure_tab(CONFIG_TAB)
        rng = f"{CONFIG_TAB}!A1:Z"
        result = (
            self._svc.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=rng)
            .execute()
        )
        if result.get("values"):
            return  # 이미 내용 있음 → 사용자 편집 보존

        rows = [
            ["설정 (B열부터 한 칸에 하나씩 입력하세요. 이 줄은 안내용)", ""],
            ["countries"] + list(defaults.get("countries", [])),
            ["categories"] + list(defaults.get("categories", [])),
            ["queries"] + list(defaults.get("queries", [])),
            ["max_total_urls", defaults.get("max_total_urls", 30)],
            ["language", defaults.get("language", "en")],
        ]
        self._svc.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=f"{CONFIG_TAB}!A1",
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()
        logger.info("설정(config) 탭을 기본값으로 채웠습니다.")

    def read_config(self) -> dict:
        """설정 탭을 읽어 dict 로 반환. 탭이 없으면 빈 dict."""
        if CONFIG_TAB not in self._existing_tabs():
            return {}
        result = (
            self._svc.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=f"{CONFIG_TAB}!A1:Z")
            .execute()
        )
        out: dict = {}
        for row in result.get("values", []):
            if not row:
                continue
            key = str(row[0]).strip().lower()
            values = [str(v).strip() for v in row[1:] if str(v).strip()]
            if key in CONFIG_LIST_KEYS:
                if values:
                    out[key] = values
            elif key in CONFIG_SCALAR_KEYS:
                if values:
                    out[key] = values[0]
        return out

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
        _join(record.get("email", [])),
        _join(record.get("instagram", [])),
    ]


def _join(value) -> str:
    """리스트면 콤마로 합치고, 문자열이면 그대로 반환."""
    if isinstance(value, list):
        return ", ".join(value)
    return str(value or "")


def _col(n: int) -> str:
    """1-indexed 컬럼 번호 → A1 표기 문자 (1->A, 27->AA)."""
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s
