"""Transcribe a video with Groq's free hosted Whisper API - backup for ElevenLabs Scribe.

Extracts mono 16kHz audio via ffmpeg, compressed to MP3 (not raw PCM) so a
long video still fits Groq's 25MB free-tier file cap, uploads with
word-level timestamps, then converts the response into the SAME schema
transcribe.py writes (words[] with type/text/start/end/speaker_id, plus
synthetic "spacing" entries for gaps) so pack_transcripts.py,
timeline_view.py, and extract_transcript.py all work unmodified.

KNOWN LIMITATIONS vs ElevenLabs Scribe (see SKILL.md Hard Rule 8 and the
Anti-patterns section - "Running Whisper locally on CPU: slow and it
normalizes fillers"; the filler-normalizing part is a Whisper model trait,
not just a local-CPU trait, so it likely still applies here even though
this runs on Groq's cloud):
  - No speaker diarization. Every word gets speaker_id=None - phrase
    grouping in pack_transcripts.py degrades to "break on silence only."
    Fine for solo talking-head footage; loses multi-speaker separation.
  - Whisper tends to smooth over disfluencies (um/uh/false starts) instead
    of transcribing verbatim. That can hide exactly the slips Chuong 2's
    "cat bo quang chet" workflow needs to see. TEST on a real
    verbal-slip-heavy clip and listen back before trusting this for class.
  - No audio-event tagging ((laughs), (applause), ...).

Cached: if the output file already exists (e.g. already transcribed by
Scribe), the upload is skipped - never silently overwrites a Scribe
transcript. Delete the file first to force a re-run with Groq.

Usage:
    python helpers/transcribe_groq.py <video_path>
    python helpers/transcribe_groq.py <video_path> --edit-dir /custom/edit
    python helpers/transcribe_groq.py <video_path> --language vi
    python helpers/transcribe_groq.py <video_path> --model whisper-large-v3-turbo
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MAX_FREE_TIER_MB = 25


def load_api_key() -> str:
    for candidate in [Path(__file__).resolve().parent.parent / ".env", Path(".env")]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "GROQ_API_KEY":
                    return v.strip().strip('"').strip("'")
    v = os.environ.get("GROQ_API_KEY", "")
    if not v:
        sys.exit("GROQ_API_KEY not found in .env or environment")
    return v


def extract_audio(video_path: Path, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def call_groq(
    audio_path: Path,
    api_key: str,
    model: str = "whisper-large-v3",
    language: str | None = None,
) -> dict:
    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FREE_TIER_MB:
        raise RuntimeError(
            f"audio is {size_mb:.1f} MB, over Groq free-tier's {MAX_FREE_TIER_MB}MB cap "
            f"- split the source video or use a paid Groq key."
        )

    data: dict[str, str] = {
        "model": model,
        "response_format": "verbose_json",
        "temperature": "0",
        "timestamp_granularities[]": "word",
    }
    if language:
        data["language"] = language

    with open(audio_path, "rb") as f:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (audio_path.name, f, "audio/mpeg")},
            data=data,
            timeout=1800,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"Groq returned {resp.status_code}: {resp.text[:500]}")

    return resp.json()


def to_scribe_schema(groq_json: dict, model: str) -> dict:
    """Convert Groq's OpenAI-style verbose_json into the Scribe-shaped schema
    the rest of the toolkit helpers expect: words[] with
    type/text/start/end/speaker_id, plus synthetic 'spacing' entries so
    pack_transcripts.py's silence-gap detection keeps working.
    """
    raw_words = groq_json.get("words")
    if raw_words is None:
        raw_words = []
        for seg in groq_json.get("segments", []):
            raw_words.extend(seg.get("words", []) or [])

    words: list[dict] = []
    prev_end = 0.0
    for w in raw_words:
        start = w.get("start")
        end = w.get("end")
        text = w.get("word", w.get("text", ""))
        if start is None or end is None:
            continue
        if start - prev_end > 0.02:
            words.append({
                "type": "spacing",
                "text": " ",
                "start": prev_end,
                "end": start,
                "speaker_id": None,
            })
        words.append({
            "type": "word",
            "text": text,
            "start": start,
            "end": end,
            "speaker_id": None,
        })
        prev_end = end

    return {
        "text": groq_json.get("text", ""),
        "language_code": groq_json.get("language"),
        "words": words,
        "engine": f"groq_{model}",
    }


def transcribe_one(
    video: Path,
    edit_dir: Path,
    api_key: str,
    model: str = "whisper-large-v3",
    language: str | None = None,
    verbose: bool = True,
) -> Path:
    """Transcribe a single video via Groq. Returns path to transcript JSON.

    Cached: returns existing path immediately if a transcript already exists
    (from Scribe or a prior Groq run) - never overwrites silently.
    """
    transcripts_dir = edit_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"

    if out_path.exists():
        if verbose:
            print(f"cached: {out_path.name}")
        return out_path

    if verbose:
        print(f"  extracting audio from {video.name}", flush=True)

    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / f"{video.stem}.mp3"
        extract_audio(video, audio)
        size_mb = audio.stat().st_size / (1024 * 1024)
        if verbose:
            print(f"  uploading {video.stem}.mp3 ({size_mb:.1f} MB) to Groq ({model})", flush=True)
        raw = call_groq(audio, api_key, model=model, language=language)

    payload = to_scribe_schema(raw, model)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    dt = time.time() - t0

    if verbose:
        kb = out_path.stat().st_size / 1024
        n_words = sum(1 for w in payload["words"] if w["type"] == "word")
        print(f"  saved: {out_path.name} ({kb:.1f} KB) in {dt:.1f}s")
        print(f"    words: {n_words:,}")

    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Transcribe a video with Groq's free hosted Whisper (backup for ElevenLabs Scribe)"
    )
    ap.add_argument("video", type=Path, help="Path to video file")
    ap.add_argument(
        "--edit-dir",
        type=Path,
        default=None,
        help="Edit output directory (default: <video_parent>/edit)",
    )
    ap.add_argument(
        "--language",
        type=str,
        default=None,
        help="Optional ISO language code (e.g., 'vi'). Omit to auto-detect.",
    )
    ap.add_argument(
        "--model",
        type=str,
        default="whisper-large-v3",
        choices=["whisper-large-v3", "whisper-large-v3-turbo"],
        help="Groq Whisper model (default: whisper-large-v3, most accurate)",
    )
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")

    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    api_key = load_api_key()

    transcribe_one(
        video=video,
        edit_dir=edit_dir,
        api_key=api_key,
        model=args.model,
        language=args.language,
    )


if __name__ == "__main__":
    main()
