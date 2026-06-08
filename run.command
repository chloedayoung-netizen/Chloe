#!/bin/bash
# 더블클릭으로 바이어 리서치를 실행하는 런처 (macOS)
# 이 파일을 프로젝트 폴더에 두고 더블클릭하면 됩니다.

cd "$(dirname "$0")" || exit 1

# 가상환경이 있으면 활성화
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "바이어 리서치를 시작합니다..."
echo "=================================="
python main.py
echo "=================================="
echo ""
echo "끝났습니다! 구글 시트를 확인하세요."
echo "이 창은 닫으셔도 됩니다."

# 창이 바로 닫히지 않게 대기
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
