# autovideo-master - Script cai dat tu dong tren Windows (PowerShell)
# Encoding: UTF-8

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      CHAO MUNG DEN VOI HE THONG AUTOVIDEO-MASTER         " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $appDir) { $appDir = (Get-Location).Path }

Write-Host "[1/6] Kiem tra moi truong he thong..." -ForegroundColor Green

# 1. Kiem tra Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning "May chua co Git! Vui long cai Git tai https://git-scm.com"
} else {
    Write-Host "  + Git: Da co ($(git --version))"
}

# 2. Kiem tra Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Warning "May chua co Node.js! Vui long cai Node.js tai https://nodejs.org"
} else {
    Write-Host "  + Node.js: Da co ($(node -v))"
}

# 3. Kiem tra Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Warning "May chua co Python! Vui long cai Python tai https://python.org"
} else {
    Write-Host "  + Python: Da co ($(python --version))"
}

# 4. Kiem tra FFmpeg
Write-Host "[2/6] Kiem tra FFmpeg & ffprobe..." -ForegroundColor Green
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpegCmd) {
    $localFfmpeg = Join-Path $appDir "bin\ffmpeg.exe"
    if (Test-Path $localFfmpeg) {
        Write-Host "  + FFmpeg: Tim thay trong bin/ cuc bo"
    } else {
        Write-Host "  + Dang tai ban FFmpeg essentials tu gyan.dev..." -ForegroundColor Yellow
        $zipPath = Join-Path $env:TEMP "ffmpeg.zip"
        Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zipPath
        Expand-Archive -Path $zipPath -DestinationPath "$env:LOCALAPPDATA\ffmpeg" -Force
        $binDir = (Get-ChildItem "$env:LOCALAPPDATA\ffmpeg\ffmpeg-*\bin" -Directory | Select-Object -First 1).FullName
        [Environment]::SetEnvironmentVariable("PATH", "$([Environment]::GetEnvironmentVariable('PATH','User'));$binDir", "User")
        $env:PATH = "$env:PATH;$binDir"
        Write-Host "  + FFmpeg da duoc cai dat vao PATH nguoi dung!"
    }
} else {
    Write-Host "  + FFmpeg: Da co tren he thong ($(ffmpeg -version | Select-Object -First 1))"
}

# 5. Kiem tra va cai dat uv
Write-Host "[3/6] Kiem tra quan ly goi uv..." -ForegroundColor Green
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  + Dang cai dat uv tu astral.sh..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}
Write-Host "  + uv: Da san sang"

# 6. Cai dat cac thu vien Python can thiet (Groq, Edge-TTS, yt-dlp)
Write-Host "[4/6] Cai dat cac thu vien Python xu ly am thanh & AI..." -ForegroundColor Green
try {
    python -m pip install --quiet --upgrade groq edge-tts yt-dlp requests
    Write-Host "  + Da cai dat/cap nhat: groq, edge-tts, yt-dlp, requests"
} catch {
    Write-Warning "Khong the cai qua pip mac dinh, thu voi uv pip..."
    uv pip install --system groq edge-tts yt-dlp requests
}

# 7. Cai dat HyperFrames qua npm
Write-Host "[5/6] Kiem tra cỗ máy dựng hình HyperFrames..." -ForegroundColor Green
if (-not (Get-Command hyperframes -ErrorAction SilentlyContinue)) {
    Write-Host "  + Dang cai dat HyperFrames CLI qua npm..." -ForegroundColor Yellow
    npm install -g hyperframes@0.7.88
}
Write-Host "  + HyperFrames: Da san sang"

# 8. Khoi tao file .env neu chua co
Write-Host "[6/6] Kiem tra file cau hinh .env..." -ForegroundColor Green
$envFile = Join-Path $appDir ".env"
$envExample = Join-Path $appDir ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Write-Host "  + Da tao file .env tu .env.example." -ForegroundColor Yellow
        Write-Host "  + VUI LONG MO FILE .env DE DIEN GROQ_API_KEY CUA BAN!" -ForegroundColor Magenta
    }
} else {
    Write-Host "  + File .env da ton tai san." -ForegroundColor Cyan
}

# Quet cac tro ly AI de ket noi skill
Write-Host "Kiem tra tro ly AI tren may..." -ForegroundColor Green
$claudeSkillDir = "$env:USERPROFILE\.claude\skills"
if (Test-Path $claudeSkillDir) {
    Write-Host "  + Phat hien Claude Code / Desktop: Ban co the su dung CLAUDE.md ngay lap tuc."
}
$agentsSkillDir = "$env:USERPROFILE\.agents\skills"
if (Test-Path $agentsSkillDir) {
    Write-Host "  + Phat hien Antigravity: Ban co the su dung AGENTS.md ngay lap tuc."
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        CAI DAT HOAN TAT! AUTOVIDEO-MASTER SAN SANG!     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Cach su dung:"
Write-Host "1. Tha video thô vao thu muc: $appDir\input"
Write-Host "2. Ra lenh cho tro ly AI (Claude / Antigravity / Codex):"
Write-Host "   'Cat loc o a, them phu de vang den va xuat video giup toi'"
Write-Host "3. Nhan video thanh pham da nen sieu net tai: $appDir\output"
Write-Host "==========================================================" -ForegroundColor Cyan
