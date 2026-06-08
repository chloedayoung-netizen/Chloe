# 해외 바이어 리서치 자동화 MVP

Clay 없이 해외 바이어(편집숍/셀렉트숍/부티크 등) 후보를 찾고, 각 회사의 공식
웹사이트에서 **입점 브랜드 / 카테고리 / 최근 신호 / 근거 문장 / 개인화 메일 첫
문장 / 연락처(이메일·인스타)**를 추출해 **Google Sheets**에 저장하는 파이프라인입니다.

```
웹 검색(Serper.dev)  →  HTML 수집(BeautifulSoup)  →
OpenAI Structured Outputs(스키마 검증)  →  연락처 수집(이메일·인스타) →
Google Sheets append(중복 제외)
```

발송 기능은 포함하지 않으며, 시트의 `status` 컬럼으로 진행 상태만 관리합니다.

---

## 프로젝트 구조

```
Chloe/
├── main.py              # 파이프라인 진입점 (검색→수집→추출→저장)
├── config.yaml          # 검색어/국가/카테고리 및 옵션
├── requirements.txt
├── .env.example         # API 키/연결정보 템플릿
├── .gitignore
├── README.md
└── src/
    ├── __init__.py
    ├── config.py        # .env + config.yaml 로딩, 쿼리 확장
    ├── search.py        # Serper.dev (Google 결과) 검색 API
    ├── fetcher.py       # HTML 수집 + 접근불가/로그인/SNS 스킵 + 연락처(이메일·인스타) 추출
    ├── schema.py        # 추출 JSON Schema (Structured Outputs)
    ├── extractor.py     # OpenAI 추출 + 스키마 검증
    └── sheets.py        # Google Sheets append + URL 중복 방지
```

---

## 1. 설치

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 채우기
```

## 2. API 준비

### 웹 검색 (Serper.dev)
> 참고: Google Programmable Search 의 무료 전체 웹 검색이 2027년 중단 예정으로,
> 신규 엔진은 사이트 50개로 제한됩니다. 그래서 전체 웹 검색이 가능한
> Serper.dev(Google 결과) 를 사용합니다.

1. [serper.dev](https://serper.dev) 가입 (구글 계정 가능)
2. 대시보드에서 **API Key** 발급 → `SERPER_API_KEY`
   - 가입 시 무료 크레딧(약 2,500 검색) 제공

### LLM (OpenRouter, OpenAI 호환)
- [OpenRouter](https://openrouter.ai/keys) 에서 API 키 발급 → `OPENROUTER_API_KEY`
- 엔드포인트는 기본값(`OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`)을 그대로 사용
- Structured Outputs(json_schema)를 지원하는 모델 사용 → `OPENROUTER_MODEL`
  (기본 `openai/gpt-4o-2024-08-06`)
- OpenAI Python SDK 를 그대로 쓰되 `base_url` 만 OpenRouter 로 지정합니다.

### Google Sheets
1. Cloud Console 에서 *Google Sheets API* 활성화
2. **서비스 계정** 생성 → JSON 키 다운로드 → `GOOGLE_SERVICE_ACCOUNT_FILE`
   경로로 저장 (예: `service_account.json`)
3. 저장할 스프레드시트를 만들고, 서비스 계정 이메일
   (`xxx@xxx.iam.gserviceaccount.com`)을 **편집자**로 공유
4. 시트 URL 의 `/d/<ID>/edit` 에서 `<ID>` → `GOOGLE_SHEET_ID`
5. 저장할 탭(워크시트) 이름 → `GOOGLE_SHEET_TAB` (기본 `buyers`)

## 3. 검색 설정

`config.yaml` 에서 검색어/국가/카테고리를 편집합니다. 쿼리의
`{country}` / `{category}` 플레이스홀더는 `countries` × `categories` 와
자동 조합됩니다.

## 4. 실행

```bash
# 저장 없이 추출 결과만 확인 (시트/서비스계정 불필요, 검색·OpenRouter 키만 필요)
python main.py --dry-run

# 실제 실행: Google Sheets 에 저장
python main.py

# 다른 설정파일로 실행
python main.py --config config.yaml

# 이미 저장된 행 중 연락처가 빈 곳만 다시 방문해 이메일/인스타 채우기
# (검색·AI 추출 없음 → 비용 0. 맥에서는 backfill_contacts.command 더블클릭)
python main.py --backfill-contacts
```

---

## Google Sheet 컬럼 설계

탭 첫 행에 아래 헤더가 자동으로 작성됩니다 (`src/sheets.py`의 `HEADERS`).

| 열 | 컬럼명 | 설명 |
|----|--------|------|
| A | `source_url` | **(필수)** 근거가 된 페이지 URL. **중복 판정 키** |
| B | `company_name` | 회사/스토어명 |
| C | `country` | 위치 국가 |
| D | `category` | 주요 취급 카테고리 |
| E | `stocked_brands` | 입점/취급 브랜드 (콤마 구분) |
| F | `recent_signal` | 최근 신호(신상 입고/신규 오픈/팝업/채용 등) |
| G | `evidence_text` | **(필수)** 판단 근거가 된 본문 인용 문장 |
| H | `personalized_opener` | 개인화 콜드메일 첫 문장 (영어 1문장) |
| I | `is_relevant_buyer` | 실제 바이어 적합 여부 (true/false) |
| J | `confidence` | 적합도 확신도 (0.0~1.0) |
| K | `status` | **`new` / `reviewed` / `contacted` / `replied`** |
| L | `search_query` | 이 후보를 찾은 검색 쿼리 |
| M | `created_at` | 저장 시각 (UTC ISO8601) |
| N | `email` | 페이지/contact 페이지에서 수집한 이메일 (콤마 구분, 없으면 빈칸) |
| O | `instagram` | 페이지에서 수집한 인스타 핸들 (콤마 구분, 없으면 빈칸) |

- 모든 행은 `source_url` 과 `evidence_text` 를 반드시 포함합니다 (둘 중 하나라도
  비면 저장하지 않음).
- 신규 저장 행의 `status` 는 항상 `new` 이며, 검수 진행에 따라 시트에서 직접
  `reviewed → contacted → replied` 로 바꿔 관리합니다.

---

## 동작 규칙 (요구사항 매핑)

| # | 요구사항 | 구현 위치 |
|---|----------|-----------|
| 1 | 검색어/국가/카테고리 설정 | `config.yaml`, `src/config.py` |
| 2 | 웹 검색 결과 수집 (Serper.dev) | `src/search.py` |
| 3 | 접근불가/로그인/에러 페이지 스킵 | `src/fetcher.py` |
| 4 | 회사/국가/카테고리/브랜드/신호/근거/메일첫문장 추출 | `src/extractor.py`, `src/schema.py` |
| 5 | JSON Schema 검증 | `src/schema.py`, `extractor._validate` |
| 6 | 시트에 한 행씩 append | `src/sheets.py` |
| 7 | 중복 URL 미저장 | `SheetClient.existing_urls` + 런타임 set |
| 8 | 모든 결과에 `source_url`/`evidence_text` 포함 | `extractor._validate`, `main.run` |
| 9 | 로그인 기반 SNS 자동 스크래핑 제외 | `fetch.blocked_domains`, `fetcher.is_blocked_domain` |
| 10 | 발송 미구현, status 관리 | `sheets.HEADERS` `status` 컬럼 |

---

## 주의 / 한계

- **로그인 기반 SNS(LinkedIn, Instagram 등) 자동 스크래핑은 하지 않습니다.**
  해당 도메인은 `config.yaml > fetch.blocked_domains` 로 차단됩니다.
- 각 사이트의 `robots.txt` 및 이용약관을 준수해 사용하세요.
- JavaScript 렌더링이 필요한 SPA 는 본문이 비어 스킵될 수 있습니다 (MVP 범위 외).
- Serper.dev 무료 크레딧 소진에 유의하세요. `config.yaml` 의
  `search.max_total_urls` 로 1회 실행량을 제한할 수 있습니다.
- `evidence_text` 는 모델에 "본문에서 그대로 인용"하도록 지시하지만, LLM 특성상
  완전 일치를 보장하진 않습니다. 검수 단계(`status`)에서 확인하세요.
```
