import os
import socket
import sys
import subprocess
import signal
import re
import logging
from funasr import AutoModel

# 屏蔽冗餘日誌，但保留 Error
logging.basicConfig(level=logging.ERROR)
os.environ["MODELSCOPE_LOG_LEVEL"] = "40"

# 配置區
MODEL_NAME = "iic/SenseVoiceSmall"
DEVICE = "cpu"
AUDIO_PATH = "/tmp/voice_input.wav"
SOCKET_PATH = "/tmp/voice_input.sock"
CACHE_DIR = "/home/askiteng/voice_input_tool/models_funasr"
LOG_FILE = "/home/askiteng/.voice_daemon.log"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{MODEL_NAME}] {msg}\n")

def load_model():
    log("Loading model...")
    try:
        return AutoModel(
            model=MODEL_NAME,
            device=DEVICE,
            disable_update=True,
            hub="ms"
        )
    except Exception as e:
        log(f"Model Load Fail: {e}")
        return None

def handle_transcription(model):
    if not os.path.exists(AUDIO_PATH):
        log(f"Audio not found: {AUDIO_PATH}")
        return
    
    try:
        # SenseVoiceSmall 識別
        res = model.generate(
            input=AUDIO_PATH,
            cache={},
            language="auto", 
            use_itn=True,
            batch_size_s=60
        )

        if res and len(res) > 0:
            text = res[0]['text']
            # 清理 SenseVoice 特有的標籤
            text = re.sub(r'<\|.*?\|>', '', text).strip()
            if text:
                # 移除中文間的空格
                text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
                log(f"Result: {text}")
                # 動態通知識別成功
                subprocess.run([
                    "notify-send", "語音輸入", "✅ 識別成功",
                    "-h", "string:x-canonical-private-synchronous:voice-input",
                    "-i", "emblem-ok-symbolic", "-t", "1000"
                ])
                # 打字
                subprocess.run(["xdotool", "type", "--clearmodifiers", text])
            else:
                subprocess.run([
                    "notify-send", "語音輸入", "⚠️ 未檢測到內容",
                    "-h", "string:x-canonical-private-synchronous:voice-input",
                    "-i", "dialog-warning", "-t", "1000"
                ])
    except Exception as e:
        log(f"Transcription Error: {e}")

def run_daemon():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    model = load_model()
    if model is None:
        return

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    log("Daemon is ready and listening.")

    try:
        while True:
            conn, _ = server.accept()
            msg = conn.recv(1024).decode()
            if msg == "PROCESS":
                handle_transcription(model)
            conn.close()
    except Exception as e:
        log(f"Runtime Fatal Error: {e}")
    finally:
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        server.close()

if __name__ == "__main__":
    run_daemon()
