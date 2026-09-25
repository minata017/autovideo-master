"""Nen video toi uu dung luong khong suy giam do net (visually near-lossless).

Cong cu nen video tu dong su dung FFmpeg voi chuan H.264 va muc CRF toi uu.
Phuc vu buoc xuat video cuoi cung trong quy trinh autovideo-master.

Cach dung:
    python nen-video.py input.mp4 -o output.mp4
    python nen-video.py input.mp4 --crf 20 --preset slow
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def tim_ffmpeg() -> str:
    """Tim duong dan ffmpeg tu bin cuc bo hoac he thong."""
    local_bin = Path(__file__).resolve().parents[2] / "bin" / "ffmpeg.exe"
    if local_bin.exists():
        return str(local_bin)
    
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
        
    raise FileNotFoundError("Khong tim thay ffmpeg trong bin/ hoac PATH he thong.")


def format_bytes(size: int) -> str:
    """Doi bytes sang chuoi de doc (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def nen_video(
    input_file: Path,
    output_file: Path | None = None,
    crf: int = 20,
    preset: str = "slow",
    audio_bitrate: str = "128k",
) -> Path:
    if not input_file.exists():
        raise FileNotFoundError(f"Khong tim thay file nguon: {input_file}")

    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}-compressed{input_file.suffix}"

    ffmpeg_bin = tim_ffmpeg()
    orig_size = input_file.stat().st_size

    print(f"[autovideo] Bat dau nen video: {input_file.name}")
    print(f"[autovideo] Dung luong goc: {format_bytes(orig_size)}")
    print(f"[autovideo] Cau hinh: CRF={crf}, Preset={preset}, Audio={audio_bitrate}")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(input_file),
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-movflags", "+faststart",
        str(output_file),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[autovideo] Loi khi nen video:\n{res.stderr}", file=sys.stderr)
        raise RuntimeError("Qua trinh nen video bang FFmpeg that bai.")

    new_size = output_file.stat().st_size
    diff_percent = (1 - (new_size / orig_size)) * 100 if orig_size > 0 else 0

    print(f"[autovideo] Nen thanh cong -> {output_file.name}")
    print(f"[autovideo] Dung luong moi: {format_bytes(new_size)}")
    print(f"[autovideo] Giam: {diff_percent:.1f}%")

    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Nen video toi uu dung luong khong suy giam do net.")
    parser.add_argument("input", type=Path, help="Duong dan file video can nen")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Duong dan file dau ra")
    parser.add_argument("--crf", type=int, default=20, help="Chi so CRF (mac dinh 20, tu 18 den 23)")
    parser.add_argument("--preset", type=str, default="slow", choices=["ultrafast", "fast", "medium", "slow", "slower"], help="Preset toc do nen")
    parser.add_argument("--audio-bitrate", type=str, default="128k", help="Bitrate am thanh (mac dinh 128k)")

    args = parser.parse_args()
    try:
        nen_video(
            input_file=args.input,
            output_file=args.output,
            crf=args.crf,
            preset=args.preset,
            audio_bitrate=args.audio_bitrate,
        )
    except Exception as e:
        print(f"Loi: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
