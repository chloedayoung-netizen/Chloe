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


def run(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    env = Env.load(require_sheets=not dry_run)
    cfg = Config.load(config_path)

    search_opts = cfg.search
    fetch_opts = cfg.fetch
    extract_opts = cfg.extract

    # OpenAI 호환 클라이언트로 OpenRouter 에 접속
    openai_client = OpenAI(api_key=env.llm_api_key, base_url=env.llm_base_url)

    # --- Sheets 준비 (dry-run 이면 건너뜀) ---
    sheet = None
    existing: set[str] = set()
    if not dry_run:
        from src.sheets import SheetClient  # 지연 import (Google 라이브러리)

        sheet = SheetClient(env.service_account_file, env.sheet_id, env.sheet_tab)
        sheet.ensure_header()
        existing = sheet.existing_urls()
        logger.info("시트에 이미 저장된 URL: %d개", len(existing))

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


def main() -> None:
    parser = argparse.ArgumentParser(description="해외 바이어 리서치 자동화 MVP")
    parser.add_argument("--config", default="config.yaml", help="config.yaml 경로")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Sheets 에 저장하지 않고 추출 결과만 로그로 확인",
    )
    args = parser.parse_args()
    run(config_path=args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
