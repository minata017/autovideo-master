param([string]$ThuMuc = "", [string]$Nguon = "", [switch]$ChiKiemTra)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$RepoUrl = 'https://github.com/minata017/autovideo-master'
function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Exe" }
}
if (-not $ThuMuc) {
    $sourceScript = $MyInvocation.MyCommand.Path
    if ($sourceScript -and (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $sourceScript) 'autovideo.py'))) {
        $ThuMuc = Split-Path -Parent $sourceScript
    } else { $ThuMuc = Join-Path $env:USERPROFILE 'autovideo-master' }
}
$ThuMuc = [System.IO.Path]::GetFullPath($ThuMuc)
$Python = Join-Path $ThuMuc '.venv\Scripts\python.exe'
if ($ChiKiemTra) {
    if (-not (Test-Path -LiteralPath $Python)) { throw 'Project .venv missing. Run installer first.' }
    Invoke-Checked $Python @((Join-Path $ThuMuc 'autovideo.py'), 'kiem-tra')
    return
}
if (-not (Test-Path -LiteralPath (Join-Path $ThuMuc 'autovideo.py'))) {
    if ((Test-Path -LiteralPath $ThuMuc) -and @(Get-ChildItem -LiteralPath $ThuMuc -Force).Count) {
        throw 'Destination is not empty and is not autovideo-master. Choose -ThuMuc.'
    }
    New-Item -ItemType Directory -Path $ThuMuc -Force | Out-Null
    if ($Nguon) {
        $Nguon = [System.IO.Path]::GetFullPath($Nguon)
        if (-not (Test-Path -LiteralPath (Join-Path $Nguon 'autovideo.py'))) { throw 'Invalid -Nguon source.' }
        foreach ($item in Get-ChildItem -LiteralPath $Nguon -Force) {
            if ($item.Name -notin @('.git','.env','.venv','temp','output','input','fonts-test')) {
                Copy-Item -LiteralPath $item.FullName -Destination $ThuMuc -Recurse -Force
            }
        }
    } else {
        $taskDownload = Join-Path $env:TEMP ('autovideo-setup-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $taskDownload | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri ($RepoUrl + '/archive/refs/heads/main.zip') -OutFile (Join-Path $taskDownload 'repo.zip')
        Expand-Archive -LiteralPath (Join-Path $taskDownload 'repo.zip') -DestinationPath $taskDownload
        foreach ($item in Get-ChildItem -LiteralPath (Join-Path $taskDownload 'autovideo-master-main') -Force) {
            Copy-Item -LiteralPath $item.FullName -Destination $ThuMuc -Recurse -Force
        }
    }
}
foreach ($dir in @('input','input\broll','output','temp','bin')) {
    New-Item -ItemType Directory -Path (Join-Path $ThuMuc $dir) -Force | Out-Null
}
if (-not (Test-Path -LiteralPath (Join-Path $ThuMuc '.env'))) {
    Copy-Item -LiteralPath (Join-Path $ThuMuc '.env.example') -Destination (Join-Path $ThuMuc '.env')
}
$Uv = Get-Command uv -ErrorAction SilentlyContinue
if ($Uv) { $UvPath = $Uv.Source } else {
    $UvPath = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
    if (-not (Test-Path -LiteralPath $UvPath)) {
        $uvScript = Join-Path $env:TEMP ('autovideo-uv-' + [guid]::NewGuid().ToString('N') + '.ps1')
        Invoke-WebRequest -UseBasicParsing -Uri 'https://astral.sh/uv/install.ps1' -OutFile $uvScript
        Invoke-Checked 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',$uvScript)
    }
}
if (-not (Test-Path -LiteralPath $UvPath)) { throw 'uv was not installed successfully.' }
if (-not (Test-Path -LiteralPath $Python)) {
    Invoke-Checked $UvPath @('venv','--python','3.13',(Join-Path $ThuMuc '.venv'))
}
Invoke-Checked $UvPath @('pip','install','--python',$Python,'-r',(Join-Path $ThuMuc 'requirements.txt'))
$Ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
$Ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
$LocalFfmpeg = Join-Path $ThuMuc 'bin\ffmpeg.exe'
$LocalFfprobe = Join-Path $ThuMuc 'bin\ffprobe.exe'
if (-not ($Ffmpeg -and $Ffprobe) -and -not ((Test-Path -LiteralPath $LocalFfmpeg) -and (Test-Path -LiteralPath $LocalFfprobe))) {
    $existingRoot = Join-Path $env:LOCALAPPDATA 'ffmpeg'
    if (Test-Path -LiteralPath $existingRoot) {
        $existingBinary = Get-ChildItem -LiteralPath $existingRoot -Recurse -File -Filter 'ffmpeg.exe' | Where-Object { Test-Path -LiteralPath (Join-Path $_.DirectoryName 'ffprobe.exe') } | Select-Object -First 1
        if ($existingBinary) {
            foreach ($name in @('ffmpeg.exe','ffprobe.exe')) {
                Copy-Item -LiteralPath (Join-Path $existingBinary.DirectoryName $name) -Destination (Join-Path $ThuMuc ('bin\' + $name)) -Force
            }
        }
    }
}
if (-not (($Ffmpeg -and $Ffprobe) -or ((Test-Path -LiteralPath $LocalFfmpeg) -and (Test-Path -LiteralPath $LocalFfprobe)))) {
    $ffDownload = Join-Path $env:TEMP ('autovideo-ffmpeg-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $ffDownload | Out-Null
    Invoke-WebRequest -UseBasicParsing -TimeoutSec 180 -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile (Join-Path $ffDownload 'ffmpeg.zip')
    Expand-Archive -LiteralPath (Join-Path $ffDownload 'ffmpeg.zip') -DestinationPath $ffDownload
    $binary = Get-ChildItem -LiteralPath $ffDownload -Recurse -File -Filter 'ffmpeg.exe' | Select-Object -First 1
    if (-not $binary) { throw 'FFmpeg archive is missing ffmpeg.exe.' }
    foreach ($name in @('ffmpeg.exe','ffprobe.exe')) {
        Copy-Item -LiteralPath (Join-Path $binary.DirectoryName $name) -Destination (Join-Path $ThuMuc ('bin\' + $name))
    }
}
Invoke-Checked $Python @((Join-Path $ThuMuc 'autovideo.py'), 'kiem-tra')
Write-Host "Installed and checked: $ThuMuc"
Write-Host 'Enter GROQ_API_KEY and PIXABAY_API_KEY in .env. Core does not require Node.js or course scripts.'
