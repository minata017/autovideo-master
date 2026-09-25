"""Transcribe a video with AssemblyAI - free-tier backup for ElevenLabs Scribe.

STANDING RULE (owner decision, 01/08/2026): this helper must ALWAYS run
AssemblyAI's best available model. Today that is universal-3-5-pro (the only
top-tier model that accepts Vietnamese; universal-3-pro silently falls back
to universal-2 for vi). When AssemblyAI ships a newer top model, upgrade the
`speech_models` list in call_assemblyai() below - and re-run the Vietnamese
accuracy test before trusting it (compare against an ElevenLabs Scribe
transcript of the same real lecture segment).

New AssemblyAI accounts get $50 in non-expiring credit (~185h of
transcription, no card required), which makes this the cheapest onboarding
path for students who have not bought ElevenLabs yet. Extracts mono 16kHz
MP3 audio via ffmpeg, uploads it, polls the transcript job, then converts
the response into the SAME schema transcribe.py writes (words[] with
type/text/start/end/speaker_id, plus synthetic "spacing" entries for gaps)
so pack_transcripts.py, timeline_view.py, and extract_transcript.py all
work unmodified.

KNOWN LIMITATIONS vs ElevenLabs Scribe (measured 01/08/2026 on a real
Vietnamese lecture segment):
  - Vietnamese accuracy is clearly below Scribe: proper nouns and
    English terms mixed into Vietnamese speech get mangled
    ("ChatGPT" -> "Chativity", "prompt" -> "Chrome", "random" -> "giam dung").
    Fine for gist-level personal notes; do NOT use for sellable course
    material - that stays on Scribe.
  - No speaker diarization here. Every word gets speaker_id=None - phrase
    grouping in pack_transcripts.py degrades to "break on silence only."
  - No audio-event tagging ((laughs), (applause), ...).

Cached: if the output file already exists (e.g. already transcribed by
Scribe), the upload is skipped - never silently overwrites a Scribe
transcript. Delete the file first to force a re-run with AssemblyAI.

Usage:
    python helpers/transcribe_assemblyai.py <video_path>
    python helpers/transcribe_assemblyai.py <video_path> --edit-dir /custom/edit
    python helpers/transcribe_assemblyai.py <video_path> --language vi
    python helpers/transcribe_assemblyai.py <video_path> --language vi --keyterms "ChatGPT,Claude Code"
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


BASE_URL = "https://api.assemblyai.com/v2"


def load_api_key() -> str:
    for candidate in [Path(__file__).resolve().parent.parent / ".env", Path(".env")]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "ASSEMBLYAI_API_KEY":
                    return v.strip().strip('"').strip("'")
    v = os.environ.get("ASSEMBLYAI_API_KEY", "")
    if not v:
        sys.exit("ASSEMBLYAI_API_KEY not found in .env or environment")
    return v


def extract_audio(video_path: Path, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def call_assemblyai(
    audio_path: Path,
    api_key: str,
    language: str | None = None,
    keyterms: list[str] | None = None,
) -> dict:
    headers = {"authorization": api_key}

    with open(audio_path, "rb") as f:
        up = requests.post(f"{BASE_URL}/upload", headers=headers, data=f, timeout=1800)
    if up.status_code != 200:
        raise RuntimeError(f"AssemblyAI upload returned {up.status_code}: {up.text[:500]}")
    audio_url = up.json()["upload_url"]

    # universal-3-5-pro is the only top-tier model that accepts Vietnamese
    # (measured 01/08/2026: universal-3-pro silently falls back to universal-2
    # for vi, producing identical output). universal-2 stays as fallback.
    body: dict = {
        "audio_url": audio_url,
        "speech_models": ["universal-3-5-pro", "universal-2"],
    }
    if keyterms:
        body["keyterms_prompt"] = keyterms
    if language:
        body["language_code"] = language
    else:
        body["language_detection"] = True

    job = requests.post(f"{BASE_URL}/transcript", headers=headers, json=body, timeout=60)
    if job.status_code != 200:
        raise RuntimeError(f"AssemblyAI transcript returned {job.status_code}: {job.text[:500]}")
    tid = job.json()["id"]

    while True:
        r = requests.get(f"{BASE_URL}/transcript/{tid}", headers=headers, timeout=60).json()
        if r["status"] == "completed":
            return r
        if r["status"] == "error":
            raise RuntimeError(f"AssemblyAI job failed: {r.get('error')}")
        time.sleep(5)


def to_scribe_schema(aai_json: dict) -> dict:
    """Convert AssemblyAI's response (word timestamps in milliseconds) into the
    Scribe-shaped schema the rest of the toolkit helpers expect."""
    words: list[dict] = []
    prev_end = 0.0
    for w in aai_json.get("words") or []:
        start = w.get("start")
        end = w.get("end")
        text = w.get("text", "")
        if start is None or end is None:
            continue
        start, end = start / 1000.0, end / 1000.0
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
        "text": aai_json.get("text", ""),
        "language_code": aai_json.get("language_code"),
        "words": words,
        "engine": "assemblyai_" + ((aai_json.get("speech_models") or ["universal"])[0]),
    }


def transcribe_one(
    video: Path,
    edit_dir: Path,
    api_key: str,
    language: str | None = None,
    keyterms: list[str] | None = None,
    verbose: bool = True,
) -> Path:
    """Transcribe a single video via AssemblyAI. Returns path to transcript JSON.

    Cached: returns existing path immediately if a transcript already exists
    (from Scribe or a prior run) - never overwrites silently.
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
            print(f"  uploading {video.stem}.mp3 ({size_mb:.1f} MB) to AssemblyAI (universal)", flush=True)
        raw = call_assemblyai(audio, api_key, language=language, keyterms=keyterms)

    payload = to_scribe_schema(raw)
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
        description="Transcribe a video with AssemblyAI Universal (free-tier backup for ElevenLabs Scribe)"
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
        "--keyterms",
        type=str,
        default=None,
        help="Comma-separated proper nouns / jargon expected in the audio "
             "(e.g., 'ChatGPT,Claude Code,Bếp Tôm'). Sharply reduces "
             "misheard brand names and mixed-in English terms.",
    )
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")

    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    api_key = load_api_key()

    keyterms = None
    if args.keyterms:
        keyterms = [t.strip() for t in args.keyterms.split(",") if t.strip()]

    transcribe_one(
        video=video,
        edit_dir=edit_dir,
        api_key=api_key,
        language=args.language,
        keyterms=keyterms,
    )


if __name__ == "__main__":
    main()
