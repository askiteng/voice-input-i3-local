#!/bin/bash

# 工具路徑
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$BASE_DIR/venv/bin/python"
DAEMON_PATH="$BASE_DIR/voice_daemon.py"
RECORDER_PATH="$BASE_DIR/voice_recorder.py"
SOCKET_PATH="/tmp/voice_input.sock"

# 1. 確保守護進程已運行
if ! pgrep -f "python.*$DAEMON_PATH" > /dev/null; then
    notify-send "語音輸入" "正在冷啟動模型 (請稍候)..." -h string:x-canonical-private-synchronous:voice-status -t 10000
    nohup $PYTHON_BIN "$DAEMON_PATH" > /dev/null 2>&1 &
    
    # 智能等待：最多等待 20 秒直到 Socket 文件出現
    MAX_RETRIES=40
    COUNT=0
    while [ ! -S "$SOCKET_PATH" ] && [ $COUNT -lt $MAX_RETRIES ]; do
        sleep 0.5
        COUNT=$((COUNT + 1))
    done
    
    if [ ! -S "$SOCKET_PATH" ]; then
        notify-send "語音輸入" "❌ 守護進程啟動超時" -t 3000
        exit 1
    fi
fi

# 2. 核心控制邏輯
echo "$(date): toggle_voice.sh triggered" >> /tmp/voice_input_debug.log
# 使用更加精確的匹配，避免匹配到當前腳本或 pgrep 進程本身
PID=$(pgrep -f "python.*$RECORDER_PATH" | grep -v "$$")

if [ -n "$PID" ]; then
    # 手動停止錄音
    echo "Stopping recorder (PID $PID)..." >> /tmp/voice_input_debug.log
    kill -SIGINT $PID
else
    # 清理舊文件並啟動錄音
    echo "Starting recorder..." >> /tmp/voice_input_debug.log
    rm -f /tmp/voice_input.raw /tmp/voice_input.wav
    $PYTHON_BIN "$RECORDER_PATH" &
fi
