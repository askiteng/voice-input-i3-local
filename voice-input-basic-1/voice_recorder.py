import os
import sys
import subprocess
import time
import math
import struct
import socket

# --- 穩健加速配置 ---
THRESHOLD = 800       
SILENCE_LIMIT = 1.0   # 說完話停頓 1.0 秒即結束，體感速度大幅提升
CHUNK_SIZE = 1024     
RATE = 16000
RAW_PATH = "/tmp/voice_input.raw"
WAV_PATH = "/tmp/voice_input.wav"
SOCKET_PATH = "/tmp/voice_input.sock"

def notify(msg, icon="audio-input-microphone"):
    subprocess.run([
        "notify-send", "語音輸入", msg,
        "-h", "string:x-canonical-private-synchronous:voice-input",
        "-i", icon, "-t", "1500"
    ])

def record_and_monitor():
    # 恢復為最穩定的 ffmpeg 管道錄音
    cmd = [
        "ffmpeg", "-y", "-f", "alsa", "-i", "plughw:1,0",
        "-ac", "1", "-ar", str(RATE), "-f", "s16le", "pipe:1"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    notify("🎙 正在錄音... (停頓 1 秒自動結束)")
    
    start_time = time.time()
    silent_chunks = 0
    max_silent_chunks = int(SILENCE_LIMIT * RATE / CHUNK_SIZE)
    
    with open(RAW_PATH, "wb") as f:
        try:
            while True:
                data = process.stdout.read(CHUNK_SIZE * 2)
                if not data: break
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
                
                if silent_chunks > max_silent_chunks and (time.time() - start_time > 0.8):
                    notify("⏸ 正在識別...", icon="media-record")
                    break
        except KeyboardInterrupt:
            pass
        finally:
            process.terminate()
            process.wait()
            
    # 極速轉換 (RAW -> WAV)
    subprocess.run([
        "ffmpeg", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "1",
        "-i", RAW_PATH, WAV_PATH
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 通知 Daemon
    if os.path.exists(SOCKET_PATH):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                s.connect(SOCKET_PATH)
                s.send(b"PROCESS")
        except:
            pass

if __name__ == "__main__":
    record_and_monitor()
