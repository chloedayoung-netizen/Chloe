"""추출 결과 JSON Schema (OpenAI Structured Outputs 용).

Structured Outputs 의 strict 모드 요구사항:
- 모든 프로퍼티가 required
- additionalProperties: false
선택값은 빈 문자열/빈 배열로 표현한다.
"""
from __future__ import annotations

# Sheets 컬럼 순서와 1:1로 매핑되는 추출 필드
EXTRACTION_FIELDS = [
    "company_name",
    "country",
    "category",
    "stocked_brands",
    "recent_signal",
    "evidence_text",
    "personalized_opener",
    "is_relevant_buyer",
    "confidence",
]

BUYER_SCHEMA = {
    "name": "buyer_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "company_name": {
                "type": "string",
                "description": "회사/스토어 이름. 불명확하면 빈 문자열.",
            },
            "country": {
                "type": "string",
                "description": "본사/매장이 위치한 국가. 불명확하면 빈 문자열.",
            },
            "category": {
                "type": "string",
                "description": "이 바이어가 다루는 주요 제품 카테고리.",
            },
            "stocked_brands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "페이지에서 확인된 입점/취급 브랜드명 목록. 없으면 빈 배열.",
            },
            "recent_signal": {
                "type": "string",
                "description": "신상 입고, 신규 오픈, 팝업, 채용 등 최근 신호. 없으면 빈 문자열.",
            },
            "evidence_text": {
                "type": "string",
                "description": "위 판단의 근거가 되는, 페이지 본문에서 그대로 인용한 문장.",
            },
            "personalized_opener": {
                "type": "string",
                "description": "이 바이어에게 보낼 콜드메일의 개인화된 첫 문장 (영어, 1문장).",
            },
            "is_relevant_buyer": {
                "type": "boolean",
                "description": "이 페이지가 우리 제품의 실제 잠재 바이어(편집숍/셀렉트숍/부티크 등)인지 여부.",
            },
            "confidence": {
                "type": "number",
                "description": "바이어 적합도 확신도 0.0~1.0.",
            },
        },
        "required": EXTRACTION_FIELDS,
    },
}
