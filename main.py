"""해외 바이어 리서치 자동화 MVP - 파이프라인 진입점.

흐름:
  config.yaml + .env 로드
    → Google Programmable Search 로 검색
    → URL HTML 수집 (접근불가/로그인/SNS 차단 도메인 스킵)
    → OpenAI Structured Outputs 로 구조화 추출 + 스키마 검증
    → Google Sheets 에 한 행씩 append (URL 중복 제외)
"""
from __future__ import annotations

import argparse
import logging

from openai import OpenAI

from src import fetcher, search
from src.config import Config, Env
from src.extractor import extract

# 주의: src.sheets 는 Google 라이브러리에 의존하므로, 실제 저장(비 dry-run)
# 시점에 지연 import 한다. → dry-run 은 Sheets 의존성 없이도 동작.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("buyer-research")


def run(
    config_path: str = "config.yaml",
    dry_run: bool = False,
    sheet_tab: str | None = None,
    use_sheet_config: bool = True,
) -> None:
    env = Env.load(require_sheets=not dry_run)
    cfg = Config.load(config_path)

    fetch_opts = cfg.fetch
    extract_opts = cfg.extract

    # OpenAI 호환 클라이언트로 OpenRouter 에 접속
    openai_client = OpenAI(api_key=env.llm_api_key, base_url=env.llm_base_url)

    # --- Sheets 준비 (dry-run 이면 건너뜀) ---
    sheet = None
    existing: set[str] = set()
    if not dry_run:
        from src.sheets import SheetClient  # 지연 import (Google 라이브러리)

        tab = sheet_tab or env.sheet_tab
        sheet = SheetClient(env.service_account_file, env.sheet_id, tab)
        sheet.ensure_header()
        existing = sheet.existing_urls()
        logger.info("시트에 이미 저장된 URL: %d개", len(existing))

        # 설정(config) 탭: 없으면 config.yaml 값으로 채우고, 있으면 그 값으로 덮어쓴다.
        # → 사용자는 터미널 대신 구글 시트에서 나라/카테고리/검색어를 바꿀 수 있다.
        # 단, 바이어 기본 모드에서만 사용한다. (다른 모드는 시트의 바이어 설정에
        #  덮어써지면 안 되므로 YAML 을 그대로 쓴다.)
        if use_sheet_config:
            sheet.ensure_config_tab(
                {
                    "countries": cfg.countries,
                    "categories": cfg.categories,
                    "queries": cfg.queries,
                    "max_total_urls": cfg.search.get("max_total_urls", 30),
                    "language": cfg.search.get("language", "en"),
                }
            )
            sheet_cfg = sheet.read_config()
            if sheet_cfg.get("countries"):
                cfg.countries = sheet_cfg["countries"]
            if sheet_cfg.get("categories"):
                cfg.categories = sheet_cfg["categories"]
            if sheet_cfg.get("queries"):
                cfg.queries = sheet_cfg["queries"]
            if sheet_cfg.get("max_total_urls"):
                cfg.search["max_total_urls"] = sheet_cfg["max_total_urls"]
            if sheet_cfg.get("language"):
                cfg.search["language"] = sheet_cfg["language"]
            logger.info(
                "설정 적용: %d개국 × %d개 카테고리 (시트 config 탭 우선)",
                len(cfg.countries),
                len(cfg.categories),
            )
        else:
            logger.info(
                "설정 적용: %d개국 × %d개 카테고리 (YAML: %s)",
                len(cfg.countries),
                len(cfg.categories),
                config_path,
            )

    search_opts = cfg.search

    # --- 1) 검색 ---
    combos = cfg.expanded_queries()
    logger.info("확장된 검색 쿼리 수: %d", len(combos))

    max_total = int(search_opts.get("max_total_urls", 60))
    per_query = int(search_opts.get("results_per_query", 10))
    hl = search_opts.get("language")  # 언어 코드 (예: "en")
    gl = search_opts.get("country_code")  # 국가 코드 (예: "fr"), 선택값

    seen_this_run: set[str] = set()
    candidates: list[search.SearchHit] = []
    for query, country, category in combos:
        if len(candidates) >= max_total:
            break
        hits = search.search(
            env.serper_api_key,
            query,
            country,
            category,
            num_results=per_query,
            gl=gl,
            hl=hl,
        )
        for hit in hits:
            url = hit.url.strip()
            if not url or url in seen_this_run or url in existing:
                continue
            # 뉴스/마켓플레이스/SNS 등 '실제 바이어가 아닌' 도메인은 발굴 단계에서 제외
            if fetcher.is_non_buyer_domain(url):
                logger.info("   ↳ 제외 (바이어 아님 도메인): %s", url)
                continue
            seen_this_run.add(url)
            candidates.append(hit)
            if len(candidates) >= max_total:
                break
    logger.info("처리할 후보 URL: %d개", len(candidates))

    # --- 2~6) 수집 → 추출 → 저장 ---
    saved = skipped_fetch = skipped_extract = 0
    blocked = fetch_opts.get("blocked_domains", [])

    for i, hit in enumerate(candidates, 1):
        logger.info("[%d/%d] %s", i, len(candidates), hit.url)

        result = fetcher.fetch(
            hit.url,
            timeout=int(fetch_opts.get("timeout_seconds", 15)),
            max_content_chars=int(fetch_opts.get("max_content_chars", 12000)),
            user_agent=fetch_opts.get("user_agent", "Mozilla/5.0"),
            blocked_domains=blocked,
        )
        if not result.ok:
            logger.info("   ↳ 스킵 (수집 불가: %s)", result.reason)
            skipped_fetch += 1
            continue

        record = extract(
            openai_client,
            env.llm_model,
            result.text,
            source_url=hit.url,
            country_hint=hit.country,
            category_hint=hit.category,
            our_brand_context=extract_opts.get("our_brand_context", ""),
            target_definition=extract_opts.get("target_definition", ""),
            temperature=float(extract_opts.get("temperature", 0.0)),
        )
        if record is None:
            logger.info("   ↳ 스킵 (추출/검증 실패)")
            skipped_extract += 1
            continue

        if not record.get("is_relevant_buyer", False):
            logger.info("   ↳ 스킵 (바이어 부적합: %s)", record.get("company_name", ""))
            skipped_extract += 1
            continue

        # 요구사항 8: source_url 과 evidence_text 강제 포함
        record["source_url"] = hit.url
        record["status"] = "new"

        # 연락처(이메일·인스타) 무료 수집. 메인 페이지에 없으면 contact 페이지 1곳 추가 확인.
        contacts = fetcher.collect_contacts(
            hit.url,
            result.html,
            timeout=int(fetch_opts.get("timeout_seconds", 15)),
            user_agent=fetch_opts.get("user_agent", "Mozilla/5.0"),
        )
        record["email"] = contacts.emails
        record["instagram"] = contacts.instagram
        if contacts.emails or contacts.instagram:
            logger.info(
                "   ↳ 연락처: %s %s",
                ", ".join(contacts.emails) or "-",
                ", ".join(contacts.instagram) or "",
            )

        if dry_run:
            logger.info(
                "   ↳ [DRY-RUN] %s | brands=%s | %s",
                record.get("company_name", ""),
                record.get("stocked_brands", []),
                record.get("evidence_text", "")[:80],
            )
            saved += 1
            continue

        assert sheet is not None
        sheet.append_row(record, search_query=hit.query)
        existing.add(hit.url)
        saved += 1
        logger.info("   ↳ 저장: %s", record.get("company_name", ""))

    logger.info(
        "완료. 저장 %d / 수집스킵 %d / 추출스킵 %d", saved, skipped_fetch, skipped_extract
    )


def backfill_contacts(config_path: str = "config.yaml", force: bool = False) -> None:
    """이미 시트에 저장된 행을 다시 방문해 이메일/인스타를 채운다.

    force=False → 연락처가 빈 행만. force=True → 모든 행(잘못 들어간 값 정정).
    검색·LLM 추출은 하지 않는다 (비용 0, source_url 만 재방문).
    """
    env = Env.load(require_sheets=True)
    cfg = Config.load(config_path)
    fetch_opts = cfg.fetch

    from src.sheets import SheetClient  # 지연 import (Google 라이브러리)

    sheet = SheetClient(env.service_account_file, env.sheet_id, env.sheet_tab)
    sheet.ensure_header()

    targets = sheet.rows_missing_contacts(force=force)
    logger.info(
        "연락처 대상 행: %d개%s", len(targets), " (force: 전체 재확인)" if force else ""
    )

    filled = 0
    for i, item in enumerate(targets, 1):
        url = item["url"]
        logger.info("[%d/%d] %s", i, len(targets), url)

        result = fetcher.fetch(
            url,
            timeout=int(fetch_opts.get("timeout_seconds", 15)),
            max_content_chars=int(fetch_opts.get("max_content_chars", 12000)),
            user_agent=fetch_opts.get("user_agent", "Mozilla/5.0"),
            blocked_domains=fetch_opts.get("blocked_domains", []),
        )
        if not result.ok:
            logger.info("   ↳ 스킵 (수집 불가: %s)", result.reason)
            continue

        contacts = fetcher.collect_contacts(
            url,
            result.html,
            timeout=int(fetch_opts.get("timeout_seconds", 15)),
            user_agent=fetch_opts.get("user_agent", "Mozilla/5.0"),
        )
        if not contacts.emails and not contacts.instagram:
            logger.info("   ↳ 연락처 없음")
            continue

        sheet.update_contacts(
            item["row"],
            ", ".join(contacts.emails),
            ", ".join(contacts.instagram),
        )
        filled += 1
        logger.info(
            "   ↳ 채움: %s %s",
            ", ".join(contacts.emails) or "-",
            ", ".join(contacts.instagram) or "",
        )

    logger.info("백필 완료. 연락처 채운 행: %d / %d", filled, len(targets))


def flag_non_buyers(config_path: str = "config.yaml") -> None:
    """이미 저장된 행 중 '바이어 아님' 도메인을 찾아 status 를 not_buyer 로 표시한다.

    삭제는 하지 않는다 — 사용자가 직접 보고 지울 수 있게 표시만 한다.
    """
    env = Env.load(require_sheets=True)
    Config.load(config_path)  # 검증용 로드 (값은 쓰지 않음)

    from src.sheets import SheetClient  # 지연 import (Google 라이브러리)

    sheet = SheetClient(env.service_account_file, env.sheet_id, env.sheet_tab)
    sheet.ensure_header()

    rows = sheet.all_rows()
    flagged = 0
    for item in rows:
        if not fetcher.is_non_buyer_domain(item["url"]):
            continue
        if item["status"] == "not_buyer":
            continue  # 이미 표시됨
        sheet.update_status(item["row"], "not_buyer")
        flagged += 1
        logger.info("표시(not_buyer): %s", item["url"])

    logger.info("완료. not_buyer 로 표시한 행: %d개", flagged)


def main() -> None:
    parser = argparse.ArgumentParser(description="해외 바이어 리서치 자동화 MVP")
    parser.add_argument("--config", default="config.yaml", help="config.yaml 경로")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Sheets 에 저장하지 않고 추출 결과만 로그로 확인",
    )
    parser.add_argument(
        "--backfill-contacts",
        action="store_true",
        help="검색 없이, 이미 저장된 행 중 연락처가 빈 곳만 다시 방문해 이메일/인스타를 채움",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="--backfill-contacts 와 함께: 연락처가 이미 있는 행도 다시 확인해 정정",
    )
    parser.add_argument(
        "--flag-non-buyers",
        action="store_true",
        help="이미 저장된 행 중 '바이어 아님' 도메인을 status=not_buyer 로 표시(삭제 안 함)",
    )
    parser.add_argument(
        "--tab",
        default=None,
        help="결과를 저장할 시트 탭 이름 (예: distributors). 비우면 .env 의 기본 탭",
    )
    args = parser.parse_args()
    if args.flag_non_buyers:
        flag_non_buyers(config_path=args.config)
    elif args.backfill_contacts:
        backfill_contacts(config_path=args.config, force=args.force)
    else:
        # 시트 config 탭(시트에서 설정 편집)은 바이어 기본 모드에서만 사용한다.
        use_sheet_config = args.config == "config.yaml"
        run(
            config_path=args.config,
            dry_run=args.dry_run,
            sheet_tab=args.tab,
            use_sheet_config=use_sheet_config,
        )


if __name__ == "__main__":
    main()
