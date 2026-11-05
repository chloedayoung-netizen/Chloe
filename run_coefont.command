#!/bin/bash
# 더블클릭으로 다국어 회의가 늘어나는 한국 기업(CoeFont 타깃)을 찾습니다.
# 결과는 시트의 coefont 탭에 따로 저장돼요.

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "CoeFont 한국 타깃 계정 리서치를 시작합니다..."
echo "=================================="
python main.py --config config.coefont.yaml --tab coefont
echo "=================================="
echo ""
echo "끝났습니다! 구글 시트의 coefont 탭을 확인하세요."
echo "이 창은 닫으셔도 됩니다."

read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
