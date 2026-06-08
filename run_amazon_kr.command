#!/bin/bash
# 더블클릭으로 '아마존에 판매 중인 한국 회사'를 찾습니다.
# 결과는 시트의 amazon_kr 탭에 따로 저장돼요 (바이어/유통사와 분리).

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "한국 아마존 셀러 리서치를 시작합니다..."
echo "=================================="
python main.py --config config.amazon-kr.yaml --tab amazon_kr
echo "=================================="
echo ""
echo "끝났습니다! 구글 시트의 amazon_kr 탭을 확인하세요."
echo "이 창은 닫으셔도 됩니다."

read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
