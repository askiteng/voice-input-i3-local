#!/bin/bash

# 工具路徑
BASE_DIR="/home/askiteng/voice_input_tool"
PYTHON_BIN="$BASE_DIR/venv/bin/python"
DAEMON_PATH="$BASE_DIR/voice_daemon.py"
RECORDER_PATH="$BASE_DIR/voice_recorder.py"
SOCKET_PATH="/tmp/voice_input.sock"

# 1. 確保守護進程已運行
if ! pgrep -f "$DAEMON_PATH" > /dev/null; then
    notify-send "語音輸入" "正在冷啟動模型 (請稍候)..." -h string:x-canonical-private-synchronous:voice-input -t 5000
    nohup $PYTHON_BIN "$DAEMON_PATH" > /dev/null 2>&1 &
    # 給予初始啟動時間
    sleep 3
fi

# 2. 核心控制邏輯
PID=$(pgrep -f "$RECORDER_PATH")
if [ -n "$PID" ]; then
    # 手動停止錄音
    pkill -SIGINT -f "$RECORDER_PATH"
else
    # 清理舊文件並啟動錄音
    rm -f /tmp/voice_input.raw /tmp/voice_input.wav
    $PYTHON_BIN "$RECORDER_PATH" &
fi
