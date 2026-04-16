import os
import sys
import subprocess
import time
import math
import struct
import socket

# --- 配置區 ---
THRESHOLD = 800       # 靜音閾值
SILENCE_LIMIT = 2.0   # 靜音持續秒數
CHUNK_SIZE = 1024     # 每次讀取的採樣數
RATE = 16000
RAW_PATH = "/tmp/voice_input.raw"
WAV_PATH = "/tmp/voice_input.wav"
SOCKET_PATH = "/tmp/voice_input.sock"

def notify(msg, icon="audio-input-microphone"):
    """發送覆蓋式通知"""
    subprocess.run([
        "notify-send", "語音輸入", msg,
        "-h", "string:x-canonical-private-synchronous:voice-input",
        "-i", icon, "-t", "2000"
    ])

def record_and_monitor():
    # 1. 啟動 ffmpeg 讀取 ALSA 並輸出原始 PCM 數據到管道
    cmd = [
        "ffmpeg", "-y", "-f", "alsa", "-i", "plughw:1,0",
        "-ac", "1", "-ar", str(RATE), "-f", "s16le", "pipe:1"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    notify("🎙 正在錄音... (停頓 2 秒自動結束)")
    
    start_time = time.time()
    silent_chunks = 0
    max_silent_chunks = int(SILENCE_LIMIT * RATE / CHUNK_SIZE)
    
    with open(RAW_PATH, "wb") as f:
        try:
            while True:
                data = process.stdout.read(CHUNK_SIZE * 2)
                if not data:
                    break
                f.write(data)
                
                count = len(data) / 2
                if count == 0: continue
                shorts = struct.unpack("%dh" % count, data)
                sum_squares = sum(s*s for s in shorts)
                rms = math.sqrt(sum_squares / count)
                
                if rms < THRESHOLD:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                
                if silent_chunks > max_silent_chunks:
                    if time.time() - start_time > 1.0:
                        notify("⏸ 檢測到停頓，正在識別...", icon="media-record")
                        break
        except KeyboardInterrupt:
            notify("⏹ 手動結束錄音", icon="media-record")
        finally:
            process.terminate()
            
    # 2. 將原始 PCM 轉換為標準 WAV (此步驟雖然慢一點但最穩定)
    subprocess.run([
        "ffmpeg", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "1",
        "-i", RAW_PATH, WAV_PATH
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. 通知 Daemon 進行轉錄
    if os.path.exists(SOCKET_PATH):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(SOCKET_PATH)
                s.send(b"PROCESS")
        except:
            pass

if __name__ == "__main__":
    record_and_monitor()
