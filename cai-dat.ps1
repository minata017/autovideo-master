# autovideo-master - Script cai dat tu dong tren Windows (PowerShell)
# Chay bang 1 dong lenh: irm https://raw.githubusercontent.com/minata017/autovideo-master/main/cai-dat.ps1 | iex
# Hoac chay truc tiep: .\cai-dat.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      AUTOVIDEO-MASTER - SCRIPT CAI DAT TU DONG          " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# BUOC 0: Xac dinh thu muc cai dat
# ============================================================
# Neu dang chay tu trong repo (da clone san) -> dung thu muc hien tai
# Neu chay qua irm | iex (khong co file path) -> clone repo vao D:\autovideo-master

$runningFromRepo = $false
$appDir = ""

# Kiem tra: script co dang nam trong repo khong?
$scriptPath = $MyInvocation.MyCommand.Path
if ($scriptPath -and (Test-Path (Join-Path (Split-Path -Parent $scriptPath) "AGENTS.md"))) {
    $appDir = Split-Path -Parent $scriptPath
    $runningFromRepo = $true
    Write-Host "[0] Phat hien ban da clone repo san tai: $appDir" -ForegroundColor Cyan
} else {
    # Chay qua irm | iex hoac khong phai tu trong repo
    $defaultDir = "D:\autovideo-master"
    Write-Host "[0] Ban dang cai tu dau. Repo se duoc clone vao: $defaultDir" -ForegroundColor Yellow

    if (Test-Path $defaultDir) {
        Write-Host "  ! Thu muc $defaultDir da ton tai. Kiem tra..." -ForegroundColor Yellow
        if (Test-Path (Join-Path $defaultDir ".git")) {
            Write-Host "  + Da co repo. Se cap nhat (git pull)..." -ForegroundColor Green
            Push-Location $defaultDir
            git pull --ff-only 2>&1 | Out-Null
            Pop-Location
            $appDir = $defaultDir
        } else {
            Write-Host "  ! Thu muc ton tai nhung khong phai repo git. Doi ten thanh .bak..." -ForegroundColor Yellow
            $backup = "$defaultDir.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Rename-Item -Path $defaultDir -NewName (Split-Path -Leaf $backup) -Force
            Write-Host "  + Da doi ten thanh: $backup"
        }
    }

    if (-not $appDir) {
        # Kiem tra Git truoc khi clone
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Host ""
            Write-Host "  LOI: May chua co Git! Vui long cai Git tai https://git-scm.com roi chay lai." -ForegroundColor Red
            exit 1
        }
        Write-Host "  + Dang clone repo tu GitHub..." -ForegroundColor Yellow
        git clone https://github.com/minata017/autovideo-master.git $defaultDir 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  LOI: Khong clone duoc repo! Kiem tra mang va thu lai." -ForegroundColor Red
            exit 1
        }
        $appDir = $defaultDir
        Write-Host "  + Clone thanh cong!" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================
# BUOC 1: Kiem tra moi truong he thong
# ============================================================
Write-Host "[1/6] Kiem tra moi truong he thong..." -ForegroundColor Green

$errors = @()

# Git
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "  + Git: Da co ($(git --version))"
} else {
    $errors += "Git"
    Write-Host "  x Git: THIEU - Cai tai https://git-scm.com" -ForegroundColor Red
}

# Node.js
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "  + Node.js: Da co ($(node -v))"
} else {
    $errors += "Node.js"
    Write-Host "  x Node.js: THIEU - Cai tai https://nodejs.org" -ForegroundColor Red
}

# Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  + Python: Da co ($(python --version))"
} else {
    $errors += "Python"
    Write-Host "  x Python: THIEU - Cai tai https://python.org" -ForegroundColor Red
}

if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Host "  CANH BAO: Thieu $($errors -join ', '). Cai truoc roi chay lai script nay." -ForegroundColor Red
    Write-Host "  Script se tiep tuc cai nhung thu con lai..." -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================
# BUOC 2: FFmpeg
# ============================================================
Write-Host "[2/6] Kiem tra FFmpeg & ffprobe..." -ForegroundColor Green
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpegCmd) {
    $localFfmpeg = Join-Path $appDir "bin\ffmpeg.exe"
    $userFfmpeg = Get-ChildItem "$env:LOCALAPPDATA\ffmpeg\ffmpeg-*\bin\ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (Test-Path $localFfmpeg) {
        Write-Host "  + FFmpeg: Tim thay trong bin/ cuc bo"
    } elseif ($userFfmpeg) {
        $binDir = $userFfmpeg.DirectoryName
        $env:PATH = "$binDir;$env:PATH"
        Write-Host "  + FFmpeg: Tim thay tai $binDir"
    } else {
        Write-Host "  + Dang tai FFmpeg tu gyan.dev (~80MB)..." -ForegroundColor Yellow
        $zipPath = Join-Path $env:TEMP "ffmpeg.zip"
        try {
            Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zipPath
            Expand-Archive -Path $zipPath -DestinationPath "$env:LOCALAPPDATA\ffmpeg" -Force
            $binDir = (Get-ChildItem "$env:LOCALAPPDATA\ffmpeg\ffmpeg-*\bin" -Directory | Select-Object -First 1).FullName
            [Environment]::SetEnvironmentVariable("PATH", "$([Environment]::GetEnvironmentVariable('PATH','User'));$binDir", "User")
            $env:PATH = "$binDir;$env:PATH"
            Write-Host "  + FFmpeg da cai xong va them vao PATH!"
        } catch {
            Write-Host "  x LOI tai FFmpeg: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  + FFmpeg: Da co tren he thong"
}

# ============================================================
# BUOC 3: uv
# ============================================================
Write-Host "[3/6] Kiem tra quan ly goi uv..." -ForegroundColor Green
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  + Dang cai dat uv tu astral.sh..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "  + uv: Da san sang"
} else {
    Write-Host "  x uv: Cai dat that bai" -ForegroundColor Red
}

# ============================================================
# BUOC 4: Thu vien Python
# ============================================================
Write-Host "[4/6] Cai dat thu vien Python (groq, edge-tts, yt-dlp, requests)..." -ForegroundColor Green
$pipResult = python -m pip install --quiet --upgrade groq edge-tts yt-dlp requests 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  + Da cai dat/cap nhat: groq, edge-tts, yt-dlp, requests"
} else {
    Write-Host "  ! pip that bai ($LASTEXITCODE), thu uv pip..." -ForegroundColor Yellow
    $uvResult = uv pip install --system groq edge-tts yt-dlp requests 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  + Da cai qua uv pip"
    } else {
        Write-Host "  x LOI: Khong cai duoc thu vien Python" -ForegroundColor Red
    }
}

# ============================================================
# BUOC 5: HyperFrames
# ============================================================
Write-Host "[5/6] Kiem tra HyperFrames..." -ForegroundColor Green
if (Get-Command node -ErrorAction SilentlyContinue) {
    if (-not (Get-Command hyperframes -ErrorAction SilentlyContinue)) {
        Write-Host "  + Dang cai dat HyperFrames qua npm..." -ForegroundColor Yellow
        npm install -g hyperframes@0.7.88 2>&1 | Out-Null
    }
    if (Get-Command hyperframes -ErrorAction SilentlyContinue) {
        Write-Host "  + HyperFrames: Da san sang"
    } else {
        Write-Host "  x HyperFrames: Cai dat that bai" -ForegroundColor Red
    }
} else {
    Write-Host "  ! Bo qua HyperFrames (can Node.js)" -ForegroundColor Yellow
}

# ============================================================
# BUOC 6: Clone script tu kho goc (khong co giay phep phan phoi lai)
# ============================================================
Write-Host "[6/6] Tai scripts tu kho goc..." -ForegroundColor Green

$toolkitScriptsDir = Join-Path $appDir "skills\autovideo-toolkit\scripts"
$captionScriptsDir = Join-Path $appDir "skills\tao-kieu-chu-caption\scripts"
$brollScriptsDir   = Join-Path $appDir "skills\dung-broll-collage\scripts"
$vendorDir         = Join-Path $appDir "skills\dung-broll-collage\vendor"

New-Item -ItemType Directory -Path $toolkitScriptsDir -Force | Out-Null
New-Item -ItemType Directory -Path $captionScriptsDir -Force | Out-Null
New-Item -ItemType Directory -Path $brollScriptsDir   -Force | Out-Null
New-Item -ItemType Directory -Path $vendorDir         -Force | Out-Null

$tempClone = Join-Path $env:TEMP "autovideo-clone-$(Get-Date -Format 'yyyyMMddHHmmss')"

$cloneOk = $true

# Clone toolkit
Write-Host "  + Clone autovideo-toolkit (10 scripts)..." -ForegroundColor Yellow
git clone --depth 1 https://github.com/sontyphu/autovideo-toolkit.git "$tempClone\toolkit" 2>$null
if ($LASTEXITCODE -eq 0) {
    Get-ChildItem "$tempClone\toolkit\viet-hoa\*.py" -ErrorAction SilentlyContinue | Copy-Item -Destination $toolkitScriptsDir -Force
} else {
    Write-Host "    ! Khong clone duoc toolkit" -ForegroundColor Yellow
    $cloneOk = $false
}

# Clone effects
Write-Host "  + Clone autovideo-effects (caption + broll + sfx)..." -ForegroundColor Yellow
git clone --depth 1 https://github.com/sontyphu/autovideo-effects.git "$tempClone\effects" 2>$null
if ($LASTEXITCODE -eq 0) {
    # Caption scripts
    Get-ChildItem "$tempClone\effects\kieu-chu-caption\scripts\*.mjs" -ErrorAction SilentlyContinue | Copy-Item -Destination $captionScriptsDir -Force
    # Broll scripts
    Get-ChildItem "$tempClone\effects\broll-collage\scripts\*.py" -ErrorAction SilentlyContinue | Copy-Item -Destination $brollScriptsDir -Force
    # GSAP vendor
    $gsapSrc = "$tempClone\effects\broll-collage\vendor\gsap.min.js"
    if (Test-Path $gsapSrc) {
        Copy-Item $gsapSrc -Destination $vendorDir -Force
    }
} else {
    Write-Host "    ! Khong clone duoc effects" -ForegroundColor Yellow
    $cloneOk = $false
}

if ($cloneOk) {
    Write-Host "  + Da tai xong tat ca scripts tu kho goc!" -ForegroundColor Green
} else {
    Write-Host "  ! Mot so scripts chua tai duoc. Tai thu cong: github.com/sontyphu" -ForegroundColor Yellow
}

# Don dep
if (Test-Path $tempClone) {
    Remove-Item -Recurse -Force $tempClone -ErrorAction SilentlyContinue
}

# ============================================================
# BUOC 7: File .env
# ============================================================
Write-Host ""
Write-Host "Kiem tra file cau hinh .env..." -ForegroundColor Green
$envFile = Join-Path $appDir ".env"
$envExample = Join-Path $appDir ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Write-Host "  + Da tao file .env tu .env.example." -ForegroundColor Yellow
        Write-Host "  + MO FILE .env VA DIEN GROQ_API_KEY CUA BAN!" -ForegroundColor Magenta
    }
} else {
    Write-Host "  + File .env da ton tai san." -ForegroundColor Cyan
}

# ============================================================
# KIEM TRA TONG THE
# ============================================================
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  KIEM TRA TONG THE                                       " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Pre-compute python import checks (can't use pipes inside hashtable)
$edgeTtsOk = $false
$groqOk = $false
$ytdlpOk = $false
try { python -c "import edge_tts" 2>$null; $edgeTtsOk = ($LASTEXITCODE -eq 0) } catch {}
try { python -c "import groq" 2>$null; $groqOk = ($LASTEXITCODE -eq 0) } catch {}
try { python -c "import yt_dlp" 2>$null; $ytdlpOk = ($LASTEXITCODE -eq 0) } catch {}

$checks = @(
    @{ Name = "Git";          OK = [bool](Get-Command git -ErrorAction SilentlyContinue) },
    @{ Name = "Python";       OK = [bool](Get-Command python -ErrorAction SilentlyContinue) },
    @{ Name = "Node.js";      OK = [bool](Get-Command node -ErrorAction SilentlyContinue) },
    @{ Name = "FFmpeg";       OK = [bool](Get-Command ffmpeg -ErrorAction SilentlyContinue) },
    @{ Name = "uv";           OK = [bool](Get-Command uv -ErrorAction SilentlyContinue) },
    @{ Name = "edge-tts";     OK = $edgeTtsOk },
    @{ Name = "groq SDK";     OK = $groqOk },
    @{ Name = "yt-dlp";       OK = $ytdlpOk },
    @{ Name = "HyperFrames";  OK = [bool](Get-Command hyperframes -ErrorAction SilentlyContinue) },
    @{ Name = ".env";         OK = (Test-Path (Join-Path $appDir ".env")) },
    @{ Name = "Toolkit scripts"; OK = (Test-Path (Join-Path $toolkitScriptsDir "transcribe_groq.py")) },
    @{ Name = "Caption scripts"; OK = (Test-Path (Join-Path $captionScriptsDir "caption.mjs")) }
)

$passed = 0; $total = $checks.Count
foreach ($c in $checks) {
    if ($c.OK) {
        Write-Host "  [OK] $($c.Name)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [!!] $($c.Name) - THIEU HOAC LOI" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  Ket qua: $passed/$total thanh phan san sang" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  THU MUC CAI DAT: $appDir" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Cach su dung:"
Write-Host "1. Tha video tho vao thu muc: $appDir\input"
Write-Host "2. Ra lenh cho tro ly AI (Claude / Antigravity / Codex):"
Write-Host "   'Cat loc o a, them phu de vang den va xuat video giup toi'"
Write-Host "3. Nhan video thanh pham da nen tai: $appDir\output"
Write-Host "==========================================================" -ForegroundColor Cyan
