import os
import sys
import subprocess
import time
import math
import struct
import socket

# --- 穩健配置 ---
THRESHOLD = 1200       
SILENCE_LIMIT = 1.0   
CHUNK_SIZE = 1024     
RATE = 16000
RAW_PATH = "/tmp/voice_input.raw"
WAV_PATH = "/tmp/voice_input.wav"
SOCKET_PATH = "/tmp/voice_input.sock"
NOTIFY_ID = "voice-status"

def notify(msg, icon="audio-input-microphone", timeout=10000):
    """覆蓋式通知：確保始終作用在同一個通知窗口"""
    subprocess.run([
        "notify-send", "語音輸入", msg,
        "-h", f"string:x-canonical-private-synchronous:{NOTIFY_ID}",
        "-i", icon, "-t", str(timeout)
    ])

def record_and_monitor():
    # 加入降噪與語音標準化：
    # highpass: 過濾低頻共振
    # afftdn: FFT 降噪
    # speechnorm: 語音音量動態標準化 (讓音量保持平衡)
    cmd = [
        "ffmpeg", "-y", "-f", "alsa", "-i", "plughw:1,0",
        "-af", "highpass=f=50,afftdn,speechnorm=e=4:r=0.0001:p=0.9",
        "-ac", "1", "-ar", str(RATE), "-f", "s16le", "pipe:1"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    notify("🎙 正在錄音... (停頓 1s 自動結束)")
    
    start_time = time.time()
    silent_chunks = 0
    max_silent_chunks = int(SILENCE_LIMIT * RATE / CHUNK_SIZE)
    data_captured = False
    
    with open(RAW_PATH, "wb") as f:
        try:
            while True:
                data = process.stdout.read(CHUNK_SIZE * 2)
                if not data: 
                    break
                f.write(data)
                data_captured = True
                
                count = len(data) / 2
                if count == 0: continue
                shorts = struct.unpack("%dh" % count, data)
                sum_squares = sum(s*s for s in shorts)
                rms = math.sqrt(sum_squares / count)
                
                if rms < THRESHOLD:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                
                if silent_chunks > max_silent_chunks and (time.time() - start_time > 0.8):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            process.terminate()
            process.wait()
            # 讀取剩餘的錯誤日誌
            err_msg = process.stderr.read().decode().strip()
            
        if not data_captured:
            notify(f"❌ 未錄製到數據: {err_msg}", icon="dialog-error", timeout=30000)
            return
            
    notify("🔄 正在轉錄內容...", icon="media-flash")
    
    subprocess.run([
        "ffmpeg", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "1",
        "-i", RAW_PATH, WAV_PATH
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 檢查文件大小
    if os.path.exists(WAV_PATH) and os.path.getsize(WAV_PATH) > 1000:
        if os.path.exists(SOCKET_PATH):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    s.connect(SOCKET_PATH)
                    s.send(b"PROCESS")
            except Exception as e:
                notify(f"❌ 無法連接守護進程: {e}", icon="dialog-error", timeout=30000)
    else:
        notify("❌ 錄音檔案損壞或太短", icon="dialog-error", timeout=30000)

if __name__ == "__main__":
    record_and_monitor()
