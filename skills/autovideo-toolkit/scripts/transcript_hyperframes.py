"""Boc chu bang ElevenLabs Scribe, xuat transcript.json dung dinh dang HyperFrames.

Thay cho lenh `npx hyperframes transcribe --model small.en` (Whisper noi bo):
  - May anh Son KHONG co whisper-cpp -> lenh goc bao "whisper_unavailable".
  - Model `small.en` la model TIENG ANH -> doc tieng Viet sai be bet.
  - Scribe boc tieng Viet chuan nhat trong cac dich vu da thu.

Dinh dang xuat: mang PHANG cac tu [{"text": ..., "start": ..., "end": ...}, ...]
(dung hop dong cua bo chen do hoa buoc 4-5: khong co "segments",
khong boc trong "words").

Moc gio cuoi duoc CLAMP theo do dai media that (tranh duoi den khi render).

Cach dung:
    python helpers/transcript_hyperframes.py <video_hoac_audio> -d <thu_muc_lam_viec>
    python helpers/transcript_hyperframes.py video.mp4 -d work --language eng
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe import call_scribe, extract_audio, load_api_key  # noqa: E402


def do_dai_media(path: Path) -> float | None:
    """Doc do dai media bang ffprobe. Tra None neu khong doc duoc."""
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=True, capture_output=True, text=True,
        )
        return float(out.stdout.strip())
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("media", type=Path, help="video hoac audio can boc chu")
    ap.add_argument("-d", "--work-dir", type=Path, required=True,
                    help="thu muc lam viec, se ghi <work-dir>/transcript.json")
    ap.add_argument("--language", default="vie",
                    help="ma ngon ngu Scribe (mac dinh vie = tieng Viet)")
    ap.add_argument("--num-speakers", type=int, default=None)
    ap.add_argument("--force", action="store_true",
                    help="boc lai du da co transcript.json")
    args = ap.parse_args()

    if not args.media.exists():
        sys.exit(f"Khong thay file: {args.media}")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.work_dir / "transcript.json"
    raw_path = args.work_dir / "transcript.scribe.json"

    if out_path.exists() and not args.force:
        print(f"da co san: {out_path} (dung --force de boc lai)")
        return

    key = load_api_key()
    t0 = time.time()

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        print(f"  tach tieng tu {args.media.name}", flush=True)
        extract_audio(args.media, wav)
        mb = wav.stat().st_size / 1_048_576
        print(f"  gui Scribe ({mb:.1f} MB, ngon ngu={args.language})", flush=True)
        data = call_scribe(wav, key, language=args.language,
                           num_speakers=args.num_speakers)

    # giu ban goc day du (co nguoi noi, su kien am thanh) de tra cuu sau
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    gioi_han = do_dai_media(args.media)
    tu_phang: list[dict] = []
    for w in data.get("words", []):
        if w.get("type") != "word":
            continue
        batdau = float(w["start"])
        ketthuc = float(w["end"])
        if gioi_han is not None:
            batdau = min(batdau, gioi_han)
            ketthuc = min(ketthuc, gioi_han)
        tu_phang.append({
            "text": w["text"],
            "start": round(batdau, 3),
            "end": round(ketthuc, 3),
        })

    if not tu_phang:
        sys.exit("Scribe khong tra ve tu nao - kiem lai file tieng")

    out_path.write_text(json.dumps(tu_phang, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    dai = tu_phang[-1]["end"]
    print(f"  xong sau {time.time()-t0:.1f}s")
    print(f"  {len(tu_phang)} tu, tu 0s den {dai:.2f}s"
          + (f" (da clamp theo media {gioi_han:.2f}s)" if gioi_han else ""))
    print(f"  ghi: {out_path}")
    print(f"  ban goc day du: {raw_path}")


if __name__ == "__main__":
    main()
