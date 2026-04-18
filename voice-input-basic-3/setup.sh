#!/bin/bash

# 獲取當前腳本所在的絕對路徑
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "=== 開始配置語音輸入工具環境 ==="

# 1. 檢查並創建虛擬環境
if [ ! -d "venv" ]; then
    echo "正在創建虛擬環境 (venv)..."
    python3 -m venv venv
else
    echo "虛擬環境 (venv) 已存在。"
fi

# 2. 安裝 Python 依賴
echo "正在安裝 Python 依賴 (這可能需要幾分鐘，取決於網路速度)..."
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

# 3. 確保腳本具有執行權限
echo "賦予腳本執行權限..."
chmod +x toggle_voice.sh

# 4. 建立模型目錄
mkdir -p models_funasr

echo "=== 配置完成 ==="
echo "提示：請在 i3wm 配置中使用以下路徑："
echo "bindsym \$mod+v exec --no-startup-id $BASE_DIR/toggle_voice.sh"
echo "第一次啟動時會下載約 300MB 的模型，請稍候。"
