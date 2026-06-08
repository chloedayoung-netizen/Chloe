#!/bin/bash
# 더블클릭으로 '경쟁 브랜드 + 최근 신호(신상/콜라보/오픈)'를 찾습니다.
# 결과는 시트의 competitors 탭에 따로 저장돼요.

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "경쟁사 모니터링을 시작합니다..."
echo "=================================="
python main.py --config config.competitors.yaml --tab competitors
echo "=================================="
echo ""
echo "끝났습니다! 구글 시트의 competitors 탭을 확인하세요."
echo "이 창은 닫으셔도 됩니다."

read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
