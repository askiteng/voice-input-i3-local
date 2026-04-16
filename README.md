# Voice Input Tool for i3wm / Linux

這是一個基於 **FunASR (SenseVoiceSmall)** 的本地語音輸入工具，專為 Linux (特別是 i3wm 用戶) 設計。它支援 VAD（語音活動檢測）、自動斷句、通知提醒，並能將語音即時轉化為文字並「打」在當前焦點視窗中。

## 🌟 特色

-   **本地處理**：無需連接網路，保護個人隱私，且延遲極低。
-   **SenseVoiceSmall**：支援中、英、日、韓等多語種自動識別，標點符號自動預測。
-   **靜音偵測**：說完話後自動結束錄音，或再次按快捷鍵手動結束。
-   **通知介面**：使用 `notify-send` 提供覆蓋式狀態提醒（🎙 錄音中 -> ⚡ 推理中 -> ✅ 完成）。
-   **無縫整合**：利用 `xdotool` 模擬鍵盤輸入，相容於瀏覽器、終端機、編輯器等任何視窗。

## 📋 系統要求

-   **Linux 操作系統** (測試環境：Ubuntu/Arch Linux)
-   **Python 3.9+** (建議 3.14)
-   **FFmpeg**：用於音訊擷取。
-   **xdotool**：用於自動鍵入文字。
-   **libnotify**：用於顯示桌面通知。

## 🛠️ 安裝說明

### 1. 安裝系統依賴

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg xdotool libnotify-bin alsa-utils

# Arch Linux
sudo pacman -S ffmpeg xdotool libnotify alsa-utils
```

### 2. 克隆項目並建立環境

```bash
git clone https://github.com/askiteng/voice-input-i3-local.git
cd voice-input-i3-local

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝 Python 依賴
pip install -r requirements.txt
```

### 3. 配置硬體

腳本預設使用 ALSA 的 `plughw:1,0` 設備。請檢查您的麥克風設備編號：

```bash
arecord -l
```

如果您的設備編號不同（例如 `hw:0,0`），請修改 `voice_recorder.py` 和 `voice_daemon.py` 中的 `ffmpeg` 命令參數。

### 4. 設定 i3wm 快捷鍵

在您的 i3 配置文件（通常是 `~/.config/i3/config`）中添加一行：

```text
# 設定 $mod+v 為觸發語音輸入 (請根據實際路徑修改)
bindsym $mod+v exec --no-startup-id /home/YOUR_USER/voice_input_tool/toggle_voice.sh
```

記得將路徑替換為您的實際安裝路徑，並賦予執行權限：
```bash
chmod +x toggle_voice.sh
```

## 🚀 使用方法

1.  按下設定的快捷鍵（如 `$mod+v`）。
2.  看到桌面通知 **🎙 正在錄音...** 後開始說話。
3.  **結束方式**：
    -   **自動**：停止說話約 1 秒，程式會自動偵測靜音並結束。
    -   **手動**：再次按下快捷鍵。
4.  通知變為 **⚡ 正在推理內容...**，稍等片刻文字即會自動出現在光標位置。

## 📂 項目結構

-   `toggle_voice.sh`: 控制中心，處理錄音啟動/停止及守護進程管理。
-   `voice_daemon.py`: 模型守護進程，預加載 FunASR 模型以加速推理。
-   `voice_recorder.py`: 錄音腳本，包含 VAD 邏輯。
-   `voice_to_text.py`: 核心識別邏輯。
-   `models_funasr/`: (自動建立) 用於存放下載的模型文件。

## ⚠️ 注意事項

-   第一次運行時，程式會從 ModelScope 下載約 300MB 的模型文件，請保持網路暢通。
-   若錄音無反應，請確認 `plughw:1,0` 是否正確，或嘗試調整 `voice_recorder.py` 中的 `THRESHOLD` 靈敏度。

## 📄 授權

MIT License
