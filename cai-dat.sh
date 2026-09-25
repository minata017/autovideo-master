#!/usr/bin/env bash
# autovideo-master - Script cai dat tu dong tren macOS / Linux
set -e

echo "=========================================================="
echo "      CHAO MUNG DEN VOI HE THONG AUTOVIDEO-MASTER         "
echo "=========================================================="

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/5] Kiem tra Git, Node.js, Python..."
command -v git >/dev/null 2>&1 || { echo "Loi: May chua co Git. Vui long cai Git!"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Loi: May chua co Node.js. Vui long cai Node.js!"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Loi: May chua co Python3. Vui long cai Python3!"; exit 1; }

echo "[2/5] Kiem tra FFmpeg..."
if ! command -v ffmpeg >/dev/null 2>&1; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Dang cai FFmpeg qua Homebrew..."
        brew install ffmpeg
    else
        echo "Dang cai FFmpeg qua apt..."
        sudo apt-get update && sudo apt-get install -y ffmpeg
    fi
fi

echo "[3/5] Cai dat thu vien Python (Groq, Edge-TTS, yt-dlp)..."
pip3 install --quiet --upgrade groq edge-tts yt-dlp requests || python3 -m pip install --quiet --upgrade groq edge-tts yt-dlp requests

echo "[4/5] Kiem tra HyperFrames..."
if ! command -v hyperframes >/dev/null 2>&1; then
    npm install -g hyperframes@0.7.88
fi

echo "[5/5] Kiem tra file cau hinh .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        echo "Da khoi tao .env tu .env.example. Vui long dien GROQ_API_KEY vao file .env!"
    fi
fi

echo "=========================================================="
echo "        CAI DAT HOAN TAT! AUTOVIDEO-MASTER SAN SANG!     "
echo "=========================================================="
