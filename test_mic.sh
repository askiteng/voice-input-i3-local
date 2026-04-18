#!/bin/bash
# 錄音測試腳本
RATE=16000
DEVICE="plughw:1,0"
OUTPUT="/tmp/mic_test.wav"

echo "🎙 正在錄音 3 秒... (已開啟 FFT 降噪 + 語音標準化)"
ffmpeg -y -f alsa -i "$DEVICE" -af "highpass=f=50,afftdn,speechnorm=e=4:r=0.0001:p=0.9" -ac 1 -ar "$RATE" -t 3 "$OUTPUT" > /dev/null 2>&1

if [ -f "$OUTPUT" ]; then
    echo "▶️ 正在播放錄音..."
    ffplay -nodisp -autoexit "$OUTPUT" > /dev/null 2>&1 || aplay "$OUTPUT"
    echo "✅ 測試完成。如果您覺得聲音太小，請執行 'alsamixer' 調整 Capture 增益。"
else
    echo "❌ 錄音失敗，請檢查設備 $DEVICE 是否正確。"
fi
