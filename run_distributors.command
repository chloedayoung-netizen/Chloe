#!/bin/bash
# 더블클릭으로 '해외 유통사/수입대행 에이전시'를 찾습니다.
# 결과는 시트의 distributors 탭에 따로 저장돼요 (바이어와 분리).

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "해외 유통사/에이전시 리서치를 시작합니다..."
echo "=================================="
python main.py --config config.distributors.yaml --tab distributors
echo "=================================="
echo ""
echo "끝났습니다! 구글 시트의 distributors 탭을 확인하세요."
echo "이 창은 닫으셔도 됩니다."

read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
