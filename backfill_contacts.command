#!/bin/bash
# 더블클릭으로, 이미 시트에 저장된 바이어 중 연락처(이메일·인스타)가
# 비어 있는 곳만 다시 방문해 채웁니다 (검색/AI 추출 없음 → 비용 0).

cd "$(dirname "$0")" || exit 1

# 가상환경이 있으면 활성화
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "기존 바이어의 연락처를 채웁니다..."
echo "=================================="
python main.py --backfill-contacts
echo "=================================="
echo ""
echo "끝났습니다! 구글 시트의 email/instagram 열을 확인하세요."
echo "이 창은 닫으셔도 됩니다."

# 창이 바로 닫히지 않게 대기
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
