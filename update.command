#!/bin/bash
# 더블클릭으로 최신 코드를 내려받아 갱신하는 업데이터 (macOS)
# 개인 파일(.env, service_account.json, config.yaml)은 건드리지 않습니다.

cd "$(dirname "$0")" || exit 1

BRANCH="claude/buyer-research-automation-mvp-RKQM8"
URL="https://github.com/chloedayoung-netizen/Chloe/archive/refs/heads/${BRANCH}.zip"

echo "최신 코드를 내려받는 중..."
TMP="$(mktemp -d)"
if ! curl -fsSL -o "$TMP/code.zip" "$URL"; then
  echo "❌ 다운로드 실패. 인터넷 연결을 확인하세요."
  rm -rf "$TMP"
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
  exit 1
fi

unzip -q -o "$TMP/code.zip" -d "$TMP"
SRC="$(find "$TMP" -maxdepth 1 -type d -name 'Chloe-*' | head -n 1)"
if [ -z "$SRC" ] || [ ! -d "$SRC/src" ]; then
  echo "❌ 압축 해제 실패."
  rm -rf "$TMP"
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
  exit 1
fi

# 코드 파일만 덮어쓰기 (개인 파일은 보존)
cp -f "$SRC/main.py" .
cp -f "$SRC/requirements.txt" .
cp -f "$SRC/run.command" . 2>/dev/null
cp -f "$SRC/update.command" . 2>/dev/null
cp -f "$SRC/schedule_install.command" . 2>/dev/null
cp -f "$SRC/schedule_remove.command" . 2>/dev/null
chmod +x ./*.command 2>/dev/null
rm -rf src && cp -Rf "$SRC/src" .
rm -rf "$TMP"

# 라이브러리 갱신
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  pip install -q -r requirements.txt
fi

echo "✅ 업데이트 완료! 이제 run.command 로 실행하세요."
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
