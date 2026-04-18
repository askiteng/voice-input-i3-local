import os
import sys
import subprocess
import signal
import re
import logging
from funasr import AutoModel

# 屏蔽冗餘日誌
logging.basicConfig(level=logging.ERROR)
os.environ["MODELSCOPE_LOG_LEVEL"] = "40"

# 配置區
# SenseVoiceSmall 適合中英日韓等多語種識別
MODEL_NAME = "iic/SenseVoiceSmall"
DEVICE = "cpu"
AUDIO_PATH = "/tmp/voice_input.wav"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_funasr")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".voice_input.log")

def record_audio():
    """使用 ffmpeg 調用 ALSA 硬體錄音"""
    cmd = [
        "ffmpeg", "-y", "-f", "alsa", "-i", "plughw:1,0",
        "-ac", "1", "-ar", "16000", AUDIO_PATH
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while True:
            if process.poll() is not None:
                break
            os.waitpid(-1, os.WNOHANG)
    except KeyboardInterrupt:
        process.send_signal(signal.SIGINT)
        process.wait()

def transcribe_and_type():
    """使用 FunASR SenseVoiceSmall 進行識別"""
    if not os.path.exists(AUDIO_PATH):
        return

    file_size = os.path.getsize(AUDIO_PATH)
    if file_size < 1000:
        return

    try:
        # 初始化 FunASR 模型
        #第一次運行會自動下載模型 (約 300MB)
        model = AutoModel(
            model=MODEL_NAME,
            device=DEVICE,
            disable_update=True,
            hub="ms" # 使用 ModelScope 下載，國內速度更快
        )

        # 進行轉錄
        # SenseVoice 不需要指定語言，它會自動感應
        res = model.generate(
            input=AUDIO_PATH,
            cache={},
            language="auto", 
            use_itn=True, # 使用 ITN 轉換數字等
            batch_size_s=60
        )

        if res and len(res) > 0:
            text = res[0]['text']
            # 清理 SenseVoice 特有的標籤 (如 <|HAPPY|>, <|zh|>)
            text = re.sub(r'<\|.*?\|>', '', text).strip()
            
            if text:
                # 移除中文間的空格
                text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
                
                # 將文字打入當前窗口
                subprocess.run(["xdotool", "type", "--clearmodifiers", text])
            else:
                with open(LOG_FILE, "a") as f:
                    f.write(f"[{MODEL_NAME}] Result is empty\n")
    except Exception as e:
        with open(LOG_FILE, "a") as f:
            f.write(f"FunASR Error: {str(e)}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--process":
        transcribe_and_type()
    else:
        record_audio()
