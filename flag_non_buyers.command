#!/bin/bash
# 더블클릭하면, 이미 시트에 저장된 행 중 '바이어가 아닌' 도메인
# (뉴스/마켓플레이스/SNS 등)을 찾아 status 열을 not_buyer 로 표시합니다.
# 삭제는 하지 않아요 — 직접 보고 지우시면 됩니다.

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "비-바이어 행을 표시합니다 (status=not_buyer)..."
echo "=================================="
python main.py --flag-non-buyers
echo "=================================="
echo ""
echo "끝났습니다! 시트에서 status 가 not_buyer 인 행을 확인 후 지우세요."
echo "이 창은 닫으셔도 됩니다."

read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
