#!/bin/bash
# 자동 실행(스케줄)을 해제합니다.

LABEL="com.chloe.buyer-research"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ -f "$PLIST" ]; then
  launchctl unload "$PLIST" 2>/dev/null
  rm -f "$PLIST"
  echo "✅ 자동 실행을 해제했습니다."
else
  echo "등록된 자동 실행이 없습니다."
fi
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
