import os
import socket
import sys
import subprocess
import signal
import re
import logging
from funasr import AutoModel

logging.basicConfig(level=logging.ERROR)
os.environ["MODELSCOPE_LOG_LEVEL"] = "40"

MODEL_NAME = "iic/SenseVoiceSmall"
DEVICE = "cpu"
AUDIO_PATH = "/tmp/voice_input.wav"
SOCKET_PATH = "/tmp/voice_input.sock"
CACHE_DIR = "/home/askiteng/voice_input_tool/models_funasr"
NOTIFY_ID = "voice-status"

def notify(msg, icon="emblem-ok-symbolic", timeout=1500):
    subprocess.run([
        "notify-send", "語音輸入", msg,
        "-h", f"string:x-canonical-private-synchronous:{NOTIFY_ID}",
        "-i", icon, "-t", str(timeout)
    ])

def handle_transcription(model):
    if not os.path.exists(AUDIO_PATH):
        return
    
    try:
        # 覆蓋之前的狀態為推理中
        notify("⚡ 正在推理內容...", icon="media-flash", timeout=5000)
        
        res = model.generate(
            input=AUDIO_PATH,
            cache={},
            language="auto", 
            use_itn=True,
            batch_size_s=60
        )

        if res and len(res) > 0:
            text = res[0]['text']
            text = re.sub(r'<\|.*?\|>', '', text).strip()
            if text:
                text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
                # 關鍵：這裡設置 1.2 秒超時，1.2秒後通知必消失
                notify("✅ 輸入完成", icon="emblem-ok-symbolic", timeout=1200)
                subprocess.run(["xdotool", "type", "--clearmodifiers", text])
                return
        
        notify("⚠️ 未檢測到內容", icon="dialog-warning", timeout=1500)
    except Exception as e:
        notify(f"❌ 錯誤: {str(e)}", icon="dialog-error", timeout=2000)

def run_daemon():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    model = AutoModel(model=MODEL_NAME, device=DEVICE, disable_update=True, hub="ms")

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)

    try:
        while True:
            conn, _ = server.accept()
            msg = conn.recv(1024).decode()
            if msg == "PROCESS":
                handle_transcription(model)
            conn.close()
    except KeyboardInterrupt:
        pass
    finally:
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        server.close()

if __name__ == "__main__":
    run_daemon()
