#!/bin/bash
# autovideo-master - Script cai dat tu dong tren macOS / Linux
# Chay bang 1 dong lenh: curl -fsSL https://raw.githubusercontent.com/minata017/autovideo-master/main/cai-dat.sh | bash
# Hoac chay truc tiep: bash cai-dat.sh

set -e

echo ""
echo "=========================================================="
echo "      AUTOVIDEO-MASTER - SCRIPT CAI DAT TU DONG          "
echo "=========================================================="
echo ""

# ============================================================
# BUOC 0: Xac dinh thu muc cai dat
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd 2>/dev/null || echo "")"
APP_DIR=""

# Kiem tra: script co nam trong repo khong?
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/AGENTS.md" ]; then
    APP_DIR="$SCRIPT_DIR"
    echo "[0] Phat hien ban da clone repo san tai: $APP_DIR"
else
    DEFAULT_DIR="$HOME/autovideo-master"
    echo "[0] Ban dang cai tu dau. Repo se duoc clone vao: $DEFAULT_DIR"

    if [ -d "$DEFAULT_DIR" ]; then
        if [ -d "$DEFAULT_DIR/.git" ]; then
            echo "  + Da co repo. Cap nhat (git pull)..."
            cd "$DEFAULT_DIR" && git pull --ff-only 2>/dev/null || true
            APP_DIR="$DEFAULT_DIR"
        else
            BACKUP="$DEFAULT_DIR.bak-$(date +%Y%m%d-%H%M%S)"
            echo "  ! Thu muc ton tai nhung khong phai repo. Doi ten thanh $BACKUP..."
            mv "$DEFAULT_DIR" "$BACKUP"
        fi
    fi

    if [ -z "$APP_DIR" ]; then
        if ! command -v git &>/dev/null; then
            echo "  LOI: May chua co Git!"
            echo "  macOS: brew install git"
            echo "  Ubuntu: sudo apt install git"
            exit 1
        fi
        echo "  + Dang clone repo tu GitHub..."
        git clone https://github.com/minata017/autovideo-master.git "$DEFAULT_DIR"
        APP_DIR="$DEFAULT_DIR"
        echo "  + Clone thanh cong!"
    fi
fi

echo ""

# ============================================================
# BUOC 1: Kiem tra moi truong
# ============================================================
echo "[1/6] Kiem tra moi truong he thong..."

ERRORS=0

if command -v git &>/dev/null; then
    echo "  + Git: $(git --version)"
else
    echo "  x Git: THIEU" && ERRORS=$((ERRORS+1))
fi

if command -v node &>/dev/null; then
    echo "  + Node.js: $(node -v)"
else
    echo "  x Node.js: THIEU" && ERRORS=$((ERRORS+1))
fi

if command -v python3 &>/dev/null; then
    echo "  + Python: $(python3 --version)"
elif command -v python &>/dev/null; then
    echo "  + Python: $(python --version)"
else
    echo "  x Python: THIEU" && ERRORS=$((ERRORS+1))
fi

PY=$(command -v python3 || command -v python || echo "python3")

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "  CANH BAO: Thieu $ERRORS thanh phan. Cai truoc roi chay lai."
    echo "  Tiep tuc cai nhung thu con lai..."
    echo ""
fi

# ============================================================
# BUOC 2: FFmpeg
# ============================================================
echo "[2/6] Kiem tra FFmpeg..."
if ! command -v ffmpeg &>/dev/null; then
    echo "  + Dang cai FFmpeg..."
    if command -v brew &>/dev/null; then
        brew install ffmpeg
    elif command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ffmpeg
    else
        echo "  x Khong tu cai duoc FFmpeg. Cai thu cong: https://ffmpeg.org"
    fi
else
    echo "  + FFmpeg: Da co"
fi

# ============================================================
# BUOC 3: uv
# ============================================================
echo "[3/6] Kiem tra uv..."
if ! command -v uv &>/dev/null; then
    echo "  + Dang cai uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  + uv: Da san sang"

# ============================================================
# BUOC 4: Thu vien Python
# ============================================================
echo "[4/6] Cai dat thu vien Python..."
$PY -m pip install --quiet --upgrade groq edge-tts yt-dlp requests 2>/dev/null || {
    echo "  ! pip that bai, thu uv pip..."
    uv pip install --system groq edge-tts yt-dlp requests 2>/dev/null || echo "  x LOI cai Python libs"
}
echo "  + Da cai: groq, edge-tts, yt-dlp, requests"

# ============================================================
# BUOC 5: HyperFrames
# ============================================================
echo "[5/6] Kiem tra HyperFrames..."
if command -v node &>/dev/null; then
    if ! command -v hyperframes &>/dev/null; then
        echo "  + Dang cai HyperFrames..."
        npm install -g hyperframes@0.7.88 2>/dev/null
    fi
    echo "  + HyperFrames: Da san sang"
else
    echo "  ! Bo qua HyperFrames (can Node.js)"
fi

# ============================================================
# BUOC 6: Clone scripts tu kho goc
# ============================================================
echo "[6/6] Tai scripts tu kho goc..."

TOOLKIT_DIR="$APP_DIR/skills/autovideo-toolkit/scripts"
CAPTION_DIR="$APP_DIR/skills/tao-kieu-chu-caption/scripts"
BROLL_DIR="$APP_DIR/skills/dung-broll-collage/scripts"
VENDOR_DIR="$APP_DIR/skills/dung-broll-collage/vendor"

mkdir -p "$TOOLKIT_DIR" "$CAPTION_DIR" "$BROLL_DIR" "$VENDOR_DIR"

TEMP_CLONE=$(mktemp -d)
trap "rm -rf $TEMP_CLONE" EXIT

echo "  + Clone autovideo-toolkit..."
git clone --depth 1 https://github.com/sontyphu/autovideo-toolkit.git "$TEMP_CLONE/toolkit" 2>/dev/null
cp "$TEMP_CLONE/toolkit/viet-hoa/"*.py "$TOOLKIT_DIR/" 2>/dev/null || true

echo "  + Clone autovideo-effects..."
git clone --depth 1 https://github.com/sontyphu/autovideo-effects.git "$TEMP_CLONE/effects" 2>/dev/null
cp "$TEMP_CLONE/effects/kieu-chu-caption/scripts/"*.mjs "$CAPTION_DIR/" 2>/dev/null || true
cp "$TEMP_CLONE/effects/broll-collage/scripts/"*.py "$BROLL_DIR/" 2>/dev/null || true
cp "$TEMP_CLONE/effects/broll-collage/vendor/gsap.min.js" "$VENDOR_DIR/" 2>/dev/null || true

echo "  + Da tai xong scripts!"

# ============================================================
# File .env
# ============================================================
echo ""
echo "Kiem tra file .env..."
if [ ! -f "$APP_DIR/.env" ] && [ -f "$APP_DIR/.env.example" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "  + Da tao .env tu .env.example"
    echo "  + MO FILE .env VA DIEN GROQ_API_KEY!"
elif [ -f "$APP_DIR/.env" ]; then
    echo "  + File .env da ton tai san"
fi

# ============================================================
# KIEM TRA TONG THE
# ============================================================
echo ""
echo "=========================================================="
echo "  KIEM TRA TONG THE"
echo "=========================================================="

PASS=0; TOTAL=0

check_item() {
    TOTAL=$((TOTAL+1))
    if eval "$2" &>/dev/null; then
        echo "  [OK] $1"
        PASS=$((PASS+1))
    else
        echo "  [!!] $1 - THIEU"
    fi
}

check_item "Git" "command -v git"
check_item "Python" "command -v python3 || command -v python"
check_item "Node.js" "command -v node"
check_item "FFmpeg" "command -v ffmpeg"
check_item "uv" "command -v uv"
check_item "edge-tts" "$PY -c 'import edge_tts'"
check_item "groq SDK" "$PY -c 'import groq'"
check_item "yt-dlp" "command -v yt-dlp"
check_item "HyperFrames" "command -v hyperframes"
check_item ".env" "test -f $APP_DIR/.env"
check_item "Toolkit scripts" "test -f $TOOLKIT_DIR/transcribe_groq.py"
check_item "Caption scripts" "test -f $CAPTION_DIR/caption.mjs"

echo ""
echo "  Ket qua: $PASS/$TOTAL thanh phan san sang"
echo ""
echo "=========================================================="
echo "  THU MUC: $APP_DIR"
echo "=========================================================="
echo "Su dung: Ra lenh cho AI tro ly (Claude / Antigravity)"
echo "=========================================================="
