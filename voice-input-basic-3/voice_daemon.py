import os
import socket
import sys
import subprocess
import signal
import re
import logging
import time
from funasr import AutoModel

logging.basicConfig(level=logging.ERROR)
os.environ["MODELSCOPE_LOG_LEVEL"] = "40"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "iic/SenseVoiceSmall"
DEVICE = "cpu"
AUDIO_PATH = "/tmp/voice_input.wav"
SOCKET_PATH = "/tmp/voice_input.sock"
CACHE_DIR = os.path.join(BASE_DIR, "models_funasr")
LOG_FILE = os.path.join(BASE_DIR, ".voice_daemon.log")
NOTIFY_ID = "voice-status"

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=LOG_FILE,
    filemode='a'
)
logger = logging.getLogger(__name__)

# 設置模型緩存環境變量
os.environ["MODELSCOPE_CACHE"] = CACHE_DIR

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
                notify("✅ 輸入完成", icon="emblem-ok-symbolic", timeout=1200)
                
                # Fcitx5 狀態切換方案
                # 1. 紀錄並關閉輸入法 (進入英文模式)
                im_status = subprocess.check_output(["fcitx5-remote"]).decode().strip()
                subprocess.run(["fcitx5-remote", "-c"])
                
                # 給予系統微小時間切換狀態，避免競爭
                time.sleep(0.1)
                
                # 2. 模擬打字 (加入 --delay 降低事件壓力)
                subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "5", text])
                
                # 3. 恢復輸入法狀態
                if im_status == "2":
                    subprocess.run(["fcitx5-remote", "-o"])
                return
        
        notify("⚠️ 未檢測到內容", icon="dialog-warning", timeout=1500)
    except Exception as e:
        notify(f"❌ 錯誤: {str(e)}", icon="dialog-error", timeout=30000)
def run_daemon():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    # 1. 先建立 Socket 並監聽，確保 recorder 能連上
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    
    # 2. 異步加載模型 (在這裡簡化為順序執行，但 Socket 已在監聽隊列中)
    logger.info(f"正在初始化模型: {MODEL_NAME} (緩存目錄: {CACHE_DIR})")
    model = None
    try:
        model = AutoModel(
            model=MODEL_NAME, 
            device=DEVICE, 
            disable_update=True, 
            hub="ms",
            ncpu=4
        )
        logger.info("模型初始化完成")
        notify("✅ 模型加載完成，隨時可以說話", timeout=2000)
    except Exception as e:
        logger.error(f"模型初始化失敗: {str(e)}")
        notify(f"❌ 模型啟動失敗: {str(e)}", icon="dialog-error", timeout=5000)
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        sys.exit(1)

    try:
        while True:
            conn, _ = server.accept()
            msg = conn.recv(1024).decode()
            if msg == "PROCESS":
                if model is not None:
                    handle_transcription(model)
                else:
                    notify("⏳ 模型仍在加載中，請稍候...", timeout=2000)
            conn.close()
    except KeyboardInterrupt:
        pass
    finally:
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        server.close()

if __name__ == "__main__":
    run_daemon()
