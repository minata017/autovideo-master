"""tao-video-tu-kich-ban.py - Tao video tu kich ban chu

Quy trinh:
  1. Doc kich ban tu file .txt hoac dung kich ban demo
  2. Tao voiceover bang Edge-TTS voi word-level timestamps
  3. Tao phu de SRT can chinh theo giong doc (tu SubMaker)
  4. Tim & chen B-roll Pixabay (neu co API key) hoac dung nen mau
  5. Ghep video + audio + phu de -> nen CRF 20 -> output/

Su dung:
  python tao-video-tu-kich-ban.py --kich-ban input/bai-noi.txt
  python tao-video-tu-kich-ban.py --kich-ban input/bai.txt --khung 16:9
  python tao-video-tu-kich-ban.py   # Dung kich ban demo
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import argparse
from pathlib import Path

# === Tim FFmpeg ===
FFMPEG = None
for candidate in [
    Path(os.environ.get("LOCALAPPDATA", "")) / "ffmpeg",
]:
    if candidate.exists():
        for f in candidate.glob("ffmpeg-*/bin/ffmpeg.exe"):
            FFMPEG = str(f)
            break
if FFMPEG is None:
    import shutil
    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

BASE_DIR = Path(__file__).resolve().parents[3]
FONT_DIR = BASE_DIR / "skills" / "tao-kieu-chu-caption" / "fonts"
FONT_FILE = FONT_DIR / "BeVietnamPro-Bold.ttf"
BROLL_SCRIPT = BASE_DIR / "skills" / "pixabay-broll" / "scripts" / "tim-broll.py"


def tim_ffprobe():
    """Tim duong dan ffprobe."""
    ffmpeg_dir = str(Path(FFMPEG).parent)
    ffprobe = os.path.join(ffmpeg_dir, "ffprobe.exe" if sys.platform == "win32" else "ffprobe")
    if os.path.exists(ffprobe):
        return ffprobe
    import shutil
    return shutil.which("ffprobe") or "ffprobe"


def lay_do_dai(media_path):
    """Lay do dai media bang ffprobe (giay)."""
    cmd = [tim_ffprobe(), "-v", "quiet", "-show_entries", "format=duration",
           "-of", "csv=p=0", str(media_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


async def tao_giong_va_phu_de(text, audio_path, srt_path, voice="vi-VN-HoaiMyNeural"):
    """Tao giong doc + phu de SRT can chinh tu SubMaker word-level timestamps.

    Tra ve: do dai audio (giay), danh sach [{"cau", "start", "end"}]
    """
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    submaker = edge_tts.SubMaker()

    # Thu word-level timestamps
    word_timings = []

    with open(audio_path, "wb") as f_audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f_audio.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                start_s = chunk["offset"] / 10_000_000
                dur_s = chunk["duration"] / 10_000_000
                word_timings.append({
                    "word": chunk["text"],
                    "start": round(start_s, 3),
                    "end": round(start_s + dur_s, 3),
                })

    # Xuat SRT tu SubMaker (da can chinh tu dong)
    srt_content = submaker.get_srt()
    Path(srt_path).write_text(srt_content, encoding="utf-8")

    duration = lay_do_dai(audio_path)
    print(f"[autovideo] Giong doc: {Path(audio_path).name} ({voice})")
    print(f"[autovideo] Do dai audio: {duration:.1f} giay")
    print(f"[autovideo] Phu de SRT: {len(srt_content.strip().split(chr(10) + chr(10)))} dong")

    # Chia thanh cac cau (de tim B-roll)
    # Gom tu thanh cau dua tren dau cham, cham hoi, cham than
    cau_list = []
    buffer_words = []
    buffer_start = 0.0

    for wt in word_timings:
        if not buffer_words:
            buffer_start = wt["start"]
        buffer_words.append(wt["word"])

        # Ket thuc cau khi gap dau cham hoac >= 8 tu
        text_so_far = " ".join(buffer_words)
        if (text_so_far.rstrip().endswith((".", "?", "!", "。"))
                or len(buffer_words) >= 12):
            cau_list.append({
                "cau": text_so_far.strip(),
                "start": buffer_start,
                "end": wt["end"],
            })
            buffer_words = []

    if buffer_words:
        cau_list.append({
            "cau": " ".join(buffer_words).strip(),
            "start": buffer_start,
            "end": word_timings[-1]["end"] if word_timings else duration,
        })

    return duration, cau_list


def tao_video_nen(duration, output_path, width=1080, height=1920):
    """Tao video nen mau gradient."""
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"color=c=#1a1a2e:s={width}x{height}:d={duration:.2f}:r=30",
        "-vf", (
            f"drawbox=x=0:y=0:w={width}:h={height//3}:color=#16213e@0.8:t=fill,"
            f"drawbox=x=0:y={height*2//3}:w={width}:h={height//3}:color=#0f3460@0.6:t=fill"
        ),
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    print(f"[autovideo] Video nen: {Path(output_path).name}")


def ghep_broll_thanh_video(broll_dir, cau_list, duration, output_path, width, height):
    """Ghep cac clip B-roll thanh 1 video lien mach theo moc thoi gian.

    Neu thieu clip cho 1 doan -> dung nen mau.
    """
    # Tao concat list
    concat_list = []
    temp_dir = Path(broll_dir).parent

    for i, cau in enumerate(cau_list):
        broll_file = Path(broll_dir) / f"broll-{i+1}.mp4"
        segment_dur = cau["end"] - cau["start"]

        if broll_file.exists():
            concat_list.append(str(broll_file))
        else:
            # Tao nen mau cho doan nay
            seg_file = temp_dir / f"nen-seg-{i+1}.mp4"
            tao_video_nen(segment_dur + 0.5, seg_file, width, height)
            concat_list.append(str(seg_file))

    if not concat_list:
        tao_video_nen(duration + 1, output_path, width, height)
        return

    # Tao file concat
    concat_txt = temp_dir / "concat-broll.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in concat_list:
            safe = str(p).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-t", str(round(duration + 0.5, 2)),
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[autovideo] LOI ghep B-roll, dung nen mau thay the")
        tao_video_nen(duration + 1, output_path, width, height)


def ghep_thanh_pham(video, audio, srt_file, output, khung):
    """Ghep video + audio + phu de SRT -> video thanh pham CRF 20."""
    # Escape path cho FFmpeg tren Windows
    srt_str = str(srt_file).replace("\\", "/")
    font_str = str(FONT_DIR).replace("\\", "/")

    if sys.platform == "win32":
        srt_esc = srt_str[0] + "\\:" + srt_str[2:]
        font_esc = font_str[0] + "\\:" + font_str[2:]
        vf = f"subtitles='{srt_esc}':fontsdir='{font_esc}'"
    else:
        vf = f"subtitles='{srt_str}':fontsdir='{font_str}'"

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
        print(f"[autovideo] Phu de SRT loi, thu ghep khong phu de...")
        cmd2 = [
            FFMPEG, "-y",
            "-i", str(video), "-i", str(audio),
            "-c:v", "libx264", "-crf", "20", "-preset", "slow",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-shortest",
            str(output)
        ]
        subprocess.run(cmd2, capture_output=True, text=True)
        print(f"[autovideo] Ghep thanh cong (khong phu de)")
    else:
        print(f"[autovideo] Ghep thanh cong voi phu de!")


def tim_broll_pixabay(cau_list, khung, temp_dir):
    """Goi tim-broll.py de tim va tai B-roll tu Pixabay.

    Tra ve: True neu tim va tai thanh cong, False neu khong co API key hoac loi.
    """
    if not BROLL_SCRIPT.exists():
        print("[autovideo] Khong tim thay script tim-broll.py")
        return False

    # Tao file canh can B-roll
    canh_file = temp_dir / "canh-can-broll.json"
    canh_data = []
    for i, c in enumerate(cau_list):
        canh_data.append({
            "cau": c["cau"],
            "start": c["start"],
            "end": c["end"],
        })

    with open(canh_file, "w", encoding="utf-8") as f:
        json.dump(canh_data, f, ensure_ascii=False, indent=2)

    # Goi tim-broll.py voi flag --tai
    cmd = [
        sys.executable, str(BROLL_SCRIPT),
        "--canh", str(canh_file),
        "--khung", khung,
        "--tai",
    ]

    print(f"\n[autovideo] Tim B-roll Pixabay cho {len(cau_list)} canh...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if "CHUA CO API KEY" in result.stdout:
        print("[autovideo] Chua co PIXABAY_API_KEY trong .env -> dung nen mau")
        return False

    if result.returncode != 0:
        print(f"[autovideo] Loi tim B-roll: {result.stderr[:300]}")
        return False

    # In ket qua
    for line in result.stdout.split("\n"):
        if line.strip():
            print(f"  {line}")

    broll_dir = temp_dir / "broll"
    return broll_dir.exists() and any(broll_dir.glob("broll-*.mp4"))


async def main():
    parser = argparse.ArgumentParser(description="Tao video tu kich ban chu")
    parser.add_argument("--kich-ban", "-k", default=None,
                        help="File .txt chua kich ban (neu bo thi dung kich ban demo)")
    parser.add_argument("--khung", default="9:16", choices=["9:16", "16:9"],
                        help="Khung hinh (mac dinh 9:16)")
    parser.add_argument("--giong", default="vi-VN-HoaiMyNeural",
                        help="Giong doc Edge-TTS (mac dinh: vi-VN-HoaiMyNeural)")
    parser.add_argument("--output", "-o", default=None,
                        help="File video dau ra (mac dinh: output/video-tu-kich-ban.mp4)")
    args = parser.parse_args()

    # Doc kich ban
    if args.kich_ban:
        kb_path = Path(args.kich_ban)
        if not kb_path.exists():
            # Thu tim trong input/
            kb_path = BASE_DIR / "input" / args.kich_ban
        if not kb_path.exists():
            print(f"[autovideo] LOI: Khong tim thay file kich ban: {args.kich_ban}")
            sys.exit(1)
        kich_ban = kb_path.read_text(encoding="utf-8").strip()
        print(f"[autovideo] Doc kich ban tu: {kb_path}")
    else:
        kich_ban = (
            "Bạn có biết rằng mỗi ngày có hàng triệu video được đăng lên mạng xã hội? "
            "Nhưng chỉ một phần rất nhỏ trong số đó thực sự thu hút được người xem. "
            "Bí quyết nằm ở ba giây đầu tiên. "
            "Nếu bạn không giữ được sự chú ý trong ba giây đầu, người ta sẽ lướt qua ngay lập tức. "
            "Hôm nay tôi sẽ chia sẻ với bạn ba mẹo đơn giản để video của bạn luôn nổi bật."
        )
        print("[autovideo] Dung kich ban demo (khong co --kich-ban)")

    # Kich thuoc theo khung hinh
    if args.khung == "9:16":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080

    temp_dir = BASE_DIR / "temp"
    output_dir = BASE_DIR / "output"
    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("  AUTOVIDEO-MASTER: Tao video tu kich ban")
    print("=" * 60)
    print(f"[autovideo] Kich ban: {len(kich_ban)} ky tu")
    print(f"[autovideo] Khung hinh: {args.khung} ({width}x{height})")
    print(f"[autovideo] FFmpeg: {FFMPEG}")

    # === Buoc 1: Tao giong doc + phu de word-level ===
    audio_file = temp_dir / "voiceover.mp3"
    srt_file = temp_dir / "phude.srt"
    duration, cau_list = await tao_giong_va_phu_de(
        kich_ban, str(audio_file), str(srt_file), args.giong
    )

    print(f"[autovideo] So cau/doan: {len(cau_list)}")

    # === Buoc 2: Tim B-roll Pixabay (neu co API key) ===
    co_broll = tim_broll_pixabay(cau_list, args.khung, temp_dir)

    # === Buoc 3: Tao video nen (B-roll hoac mau) ===
    video_nen = temp_dir / "video-nen.mp4"
    if co_broll:
        broll_dir = temp_dir / "broll"
        ghep_broll_thanh_video(broll_dir, cau_list, duration, video_nen, width, height)
        print(f"[autovideo] Video nen: B-roll Pixabay")
    else:
        tao_video_nen(duration + 1, video_nen, width, height)

    # === Buoc 4: Ghep thanh pham ===
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = output_dir / "video-tu-kich-ban.mp4"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    ghep_thanh_pham(video_nen, audio_file, srt_file, output_file, args.khung)

    # === Bao cao ===
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\n{'=' * 60}")
        print(f"  HOAN TAT!")
        print(f"  Video: {output_file}")
        print(f"  Dung luong: {size_mb:.2f} MB")
        print(f"  Do dai: {duration:.1f} giay")
        print(f"  Khung hinh: {args.khung} ({width}x{height})")
        print(f"  Phu de: can chinh theo giong doc (word-level)")
        print(f"  B-roll: {'Pixabay' if co_broll else 'Nen mau (chua co API key)'}")
        print(f"{'=' * 60}")
    else:
        print("[autovideo] LOI: Khong tao duoc video!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
