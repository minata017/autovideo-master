"""tao-video-tu-kich-ban.py - Quy trinh tao video tu kich ban chu (Edge-TTS + FFmpeg)

Buoc 1: Nhan kich ban text
Buoc 2: Tao voiceover bang Edge-TTS (0 dong)
Buoc 3: Tao video nen mau + phu de ASS tu dong
Buoc 4: Nen video CRF 20 xuat ra output/
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Duong dan FFmpeg
FFMPEG = None
for candidate in [
    Path(__file__).resolve().parents[1] / "bin" / "ffmpeg.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "ffmpeg" / "ffmpeg-9.0.2-essentials_build" / "bin" / "ffmpeg.exe",
]:
    if candidate.exists():
        FFMPEG = str(candidate)
        break
if FFMPEG is None:
    import shutil
    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

FONT_DIR = Path(__file__).resolve().parents[3] / "skills" / "tao-kieu-chu-caption" / "fonts"
FONT_FILE = FONT_DIR / "BeVietnamPro-Bold.ttf"


async def tao_giong_doc(text: str, output_audio: Path, voice: str = "vi-VN-HoaiMyNeural"):
    """Tao file audio tu van ban bang Edge-TTS."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_audio))
    print(f"[autovideo] Giong doc: {output_audio.name} ({voice})")


def lay_do_dai_audio(audio_path: Path) -> float:
    """Lay do dai audio bang ffprobe."""
    ffmpeg_dir = str(Path(FFMPEG).parent)
    ffprobe = os.path.join(ffmpeg_dir, "ffprobe.exe") if sys.platform == "win32" else os.path.join(ffmpeg_dir, "ffprobe")
    if not os.path.exists(ffprobe):
        import shutil
        ffprobe = shutil.which("ffprobe") or "ffprobe"
    cmd = [ffprobe, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def tao_file_ass(text: str, duration: float, output_ass: Path, font_name: str = "Be Vietnam Pro"):
    """Tao file phu de ASS don gian."""
    # Chia text thanh cac dong ngan
    words = text.split()
    lines = []
    current = []
    for w in words:
        current.append(w)
        if len(" ".join(current)) > 30:
            lines.append(" ".join(current))
            current = []
    if current:
        lines.append(" ".join(current))

    # Chia deu thoi gian
    time_per_line = duration / len(lines) if lines else duration

    events = []
    for i, line in enumerate(lines):
        start = i * time_per_line
        end = (i + 1) * time_per_line
        sh, sm, ss = int(start // 3600), int((start % 3600) // 60), start % 60
        eh, em, es = int(end // 3600), int((end % 3600) // 60), end % 60
        events.append(
            f"Dialogue: 0,{sh}:{sm:02d}:{ss:05.2f},{eh}:{em:02d}:{es:05.2f},Default,,0,0,0,,{line}"
        )

    ass_content = f"""[Script Info]
Title: autovideo-master caption
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events)

    output_ass.write_text(ass_content, encoding="utf-8")
    print(f"[autovideo] Phu de: {output_ass.name} ({len(lines)} dong)")


def tao_video_nen(duration: float, output_video: Path, width: int = 1080, height: int = 1920):
    """Tao video nen mau gradient 9:16."""
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"color=c=#1a1a2e:s={width}x{height}:d={duration:.2f}:r=30",
        "-vf", f"drawbox=x=0:y=0:w={width}:h={height//3}:color=#16213e@0.8:t=fill,"
               f"drawbox=x=0:y={height*2//3}:w={width}:h={height//3}:color=#0f3460@0.6:t=fill",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_video)
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    print(f"[autovideo] Video nen: {output_video.name}")


def ghep_video_audio_phude(video: Path, audio: Path, ass_file: Path, output: Path):
    """Ghep video nen + audio + phu de ASS -> video thanh pham."""
    # FFmpeg tren Windows can escape dau : va \ dac biet trong filter
    ass_str = str(ass_file).replace("\\", "/")
    font_dir_str = str(FONT_DIR).replace("\\", "/")

    # Cú phap da test thanh cong: subtitles='D\:/path':fontsdir='D\:/path'
    if sys.platform == "win32":
        # Escape drive letter colon chi 1 lan
        ass_esc = ass_str[0] + "\\:" + ass_str[2:]  # D: -> D\:
        font_esc = font_dir_str[0] + "\\:" + font_dir_str[2:]
        vf = f"subtitles='{ass_esc}':fontsdir='{font_esc}'"
    else:
        vf = f"subtitles='{ass_str}':fontsdir='{font_dir_str}'"

    cmd = [
        FFMPEG, "-y",
        "-i", str(video),
        "-i", str(audio),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-preset", "slow",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-shortest",
        str(output)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"[autovideo] LOI ghep voi phu de: {result.stderr[-500:]}", file=sys.stderr)
        # Fallback: ghep khong phu de
        cmd2 = [
            FFMPEG, "-y",
            "-i", str(video), "-i", str(audio),
            "-c:v", "libx264", "-crf", "20", "-preset", "slow",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-shortest",
            str(output)
        ]
        subprocess.run(cmd2, capture_output=True, text=True)
        print(f"[autovideo] Ghep thanh cong (khong co phu de do loi ASS)")
    else:
        print(f"[autovideo] Ghep thanh cong voi phu de!")


async def main():
    base_dir = Path(__file__).resolve().parents[3]  # scripts -> autovideo-toolkit -> skills -> project root
    temp_dir = base_dir / "temp"
    output_dir = base_dir / "output"
    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # Kich ban mau
    kich_ban = (
        "Bạn có biết rằng mỗi ngày có hàng triệu video được đăng lên mạng xã hội? "
        "Nhưng chỉ một phần rất nhỏ trong số đó thực sự thu hút được người xem. "
        "Bí quyết nằm ở ba giây đầu tiên. "
        "Nếu bạn không giữ được sự chú ý trong ba giây đầu, người ta sẽ lướt qua ngay lập tức. "
        "Hôm nay tôi sẽ chia sẻ với bạn ba mẹo đơn giản để video của bạn luôn nổi bật."
    )

    print("=" * 60)
    print("  AUTOVIDEO-MASTER: Tao video tu kich ban")
    print("=" * 60)
    print(f"[autovideo] Kich ban: {len(kich_ban)} ky tu")
    print(f"[autovideo] FFmpeg: {FFMPEG}")

    # Buoc 1: Tao giong doc
    audio_file = temp_dir / "voiceover.mp3"
    await tao_giong_doc(kich_ban, audio_file)

    # Buoc 2: Lay do dai audio
    duration = lay_do_dai_audio(audio_file)
    print(f"[autovideo] Do dai audio: {duration:.1f} giay")

    # Buoc 3: Tao video nen 9:16
    video_nen = temp_dir / "video-nen.mp4"
    tao_video_nen(duration + 1, video_nen)

    # Buoc 4: Tao phu de ASS
    ass_file = temp_dir / "phude.ass"
    tao_file_ass(kich_ban, duration, ass_file)

    # Buoc 5: Ghep + Nen CRF 20
    output_file = output_dir / "video-tu-kich-ban-demo.mp4"
    ghep_video_audio_phude(video_nen, audio_file, ass_file, output_file)

    # Bao cao
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\n{'=' * 60}")
        print(f"  HOAN TAT!")
        print(f"  Video: {output_file}")
        print(f"  Dung luong: {size_mb:.2f} MB")
        print(f"  Do dai: {duration:.1f} giay")
        print(f"  Dinh dang: 9:16 (1080x1920)")
        print(f"{'=' * 60}")
    else:
        print("[autovideo] LOI: Khong tao duoc video!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
