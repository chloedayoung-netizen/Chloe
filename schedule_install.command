#!/bin/bash
# 매일 정해진 시간에 바이어 리서치를 자동 실행하도록 등록 (macOS launchd)
# 더블클릭하면 실행할 시간을 묻고 등록합니다.

cd "$(dirname "$0")" || exit 1
PROJ="$(pwd)"

# 파이썬 경로 (가상환경 우선)
PY="$PROJ/.venv/bin/python"
if [ ! -x "$PY" ]; then PY="$(command -v python3)"; fi

# 실행 시간 입력받기
echo "매일 몇 시에 자동 실행할까요?"
read -r -p "시(0~23, 그냥 엔터 치면 9시): " HOUR
if [ -z "$HOUR" ]; then HOUR=9; fi

LABEL="com.chloe.buyer-research"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$PROJ/main.py</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJ</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>$HOUR</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key><string>$PROJ/schedule.log</string>
  <key>StandardErrorPath</key><string>$PROJ/schedule.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST"

echo ""
echo "✅ 매일 ${HOUR}시에 자동 실행되도록 등록했습니다."
echo "   (맥이 켜져 있어야 실행됩니다. 결과/오류는 schedule.log 에 기록돼요.)"
echo "   끄고 싶으면 schedule_remove.command 를 더블클릭하세요."
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
