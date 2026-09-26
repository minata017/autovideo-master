#!/usr/bin/env python3
"""autovideo-master: independent, reviewable video creation and editing."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import html
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
FPS = 30
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


class VideoError(Exception):
    pass


def config():
    p = Path(os.environ.get("AUTOVIDEO_ENV_FILE", str(ROOT / ".env")))
    result = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", line)
            if m:
                value = m[2]
                if value.startswith(('"', "'")) and value[-1:] == value[:1]:
                    value = value[1:-1]
                else:
                    value = value.split(" #", 1)[0].rstrip()
                result[m[1]] = value
    for key in ("GROQ_API_KEY", "PIXABAY_API_KEY", "ELEVENLABS_API_KEY"):
        if os.environ.get(key):
            result[key] = os.environ[key]
    return result


def clean_error(value):
    value = str(value)
    for key, secret in config().items():
        if ("KEY" in key or "TOKEN" in key) and secret:
            value = value.replace(secret, "[khóa đã ẩn]")
    return re.sub(r"([?&]key=)[^&\s]+", r"\1[khóa đã ẩn]", value)


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def tool(name):
    extension = ".exe" if os.name == "nt" else ""
    choices = [ROOT / "bin" / (name + extension)]
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        choices += sorted(Path(os.environ["LOCALAPPDATA"]).glob(f"ffmpeg/ffmpeg-*/bin/{name}.exe"), reverse=True)
    for path in choices:
        if path.is_file():
            return str(path)
    found = shutil.which(name)
    if found:
        return found
    raise VideoError(f"Thiếu {name}. Chạy cai-dat.ps1 hoặc cai-dat.sh.")


def run(args, timeout=1800):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise VideoError(clean_error(result.stderr[-1800:] or result.stdout[-1800:]))
    return result


def probe(path):
    data = json.loads(run([tool("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", path]).stdout)
    duration = float(data["format"].get("duration", 0))
    if not math.isfinite(duration) or duration <= 0:
        raise VideoError(f"Không đọc được thời lượng: {Path(path).name}")
    return {"duration": duration, "size": int(data["format"].get("size", 0)),
            "video": next((s for s in data["streams"] if s["codec_type"] == "video"), None),
            "audio": next((s for s in data["streams"] if s["codec_type"] == "audio"), None)}


def make_job(mode):
    name = time.strftime("%Y%m%d-%H%M%S") + "-" + mode + "-" + uuid.uuid4().hex[:6]
    path = ROOT / "output" / name
    path.mkdir(parents=True)
    return path


def stamp(seconds, ass=False):
    units = max(0, round(seconds * (100 if ass else 1000)))
    scale = 100 if ass else 1000
    whole, frac = divmod(units, scale)
    h, rest = divmod(whole, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}.{frac:02d}" if ass else f"{h:02d}:{m:02d}:{s:02d},{frac:03d}"


def normalize(word):
    return re.sub(r"[^\w]", "", html.unescape(word).casefold(), flags=re.UNICODE)


def restore_punctuation(words, text):
    tokens = text.split()
    cursor = 0
    for word in words:
        needle = normalize(word["text"])
        for j in range(cursor, min(cursor + 8, len(tokens))):
            if normalize(tokens[j]) == needle:
                word["text"] = tokens[j]
                cursor = j + 1
                break
    return words


def caption_groups(words, duration):
    groups, pending = [], []
    for raw in words:
        word = {"text": html.unescape(str(raw["text"])).strip(),
                "start": max(0, float(raw["start"])), "end": min(duration, float(raw["end"]))}
        if not word["text"] or word["end"] <= word["start"]:
            continue
        if pending and (len(" ".join(w["text"] for w in pending) + " " + word["text"]) > 36
                        or word["start"] - pending[-1]["end"] > .4):
            groups.append(pending)
            pending = []
        pending.append(word)
        if len(pending) >= 5 or re.search(r"[.!?;:]$", word["text"]):
            groups.append(pending)
            pending = []
    if pending:
        groups.append(pending)
    return [{"start": group[0]["start"], "end": group[-1]["end"],
             "text": " ".join(w["text"] for w in group), "words": group} for group in groups]


def write_captions(job, words, duration, width, height, style="vang-den"):
    groups = caption_groups(words, duration)
    srt = "\n\n".join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i, c in enumerate(groups, 1))
    (job / "phu-de.srt").write_text(srt + "\n", encoding="utf-8")
    font_size = round(height * (.034 if height > width else .065))
    color = "&H0000EFFF" if style in ("vang-den", "karaoke") else "&H00FFFFFF"
    border = 3 if style == "nen-den" else 1
    outline = 1 if style == "toi-gian" else 2
    body = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {width}\nPlayResY: {height}\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Default,Be Vietnam Pro,{font_size},{color},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,{border},{outline},0,2,{round(width*.06)},{round(width*.06)},{round(height*.12)},1\n"
            "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    for c in groups:
        text = c["text"].replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")
        if style == "shorts":
            text = text.upper()
        elif style == "karaoke":
            pieces = []
            for i, word in enumerate(c["words"]):
                until = c["words"][i+1]["start"] if i+1 < len(c["words"]) else c["end"]
                length = max(1, round((until-word["start"])*100))
                safe = word["text"].replace("\\", "").replace("{", "(").replace("}", ")")
                pieces.append(f"{{\\k{length}}}{safe}")
            text = " ".join(pieces)
        body += f"Dialogue: 0,{stamp(c['start'], True)},{stamp(c['end'], True)},Default,,0,0,0,,{text}\n"
    (job / "phu-de.ass").write_text(body, encoding="utf-8-sig")
    return groups


async def tts(text, job, voice):
    import edge_tts
    words = []
    with (job / "giong-doc.mp3").open("wb") as audio:
        async for chunk in edge_tts.Communicate(text, voice, boundary="WordBoundary").stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"text": chunk["text"], "start": chunk["offset"] / 1e7,
                              "end": (chunk["offset"] + chunk["duration"]) / 1e7})
    if not words:
        raise VideoError("Giọng đọc không trả về mốc từ; chưa tạo được phụ đề căn lời.")
    return restore_punctuation(words, text), probe(job / "giong-doc.mp3")["duration"]


def build_scenes(words, duration):
    scenes, group = [], []
    for word in words:
        group.append(word)
        if (re.search(r"[.!?]$", word["text"]) and word["end"] - group[0]["start"] >= 1.2) or len(group) >= 28:
            scenes.append({"text": " ".join(w["text"] for w in group), "boundary": word["end"]})
            group = []
    if group:
        scenes.append({"text": " ".join(w["text"] for w in group), "boundary": duration})
    start = 0
    for i, scene in enumerate(scenes):
        end = duration if i == len(scenes) - 1 else min(duration, scene.pop("boundary"))
        scene.pop("boundary", None)
        scene.update(id=i + 1, start=round(start, 6), end=round(end, 6), keyword="", selected=None, candidates=[])
        start = end
    return scenes


KEYWORDS = {"trí tuệ nhân tạo": "artificial intelligence", "công cụ ai": "artificial intelligence computer",
            "sáng tạo nội dung": "video editing", "kịch bản": "writing script", "giọng nói": "microphone recording",
            "video": "video editing computer", "kinh doanh": "business meeting", "học": "student learning",
            "gia đình": "family", "sức khỏe": "exercise", "tài chính": "finance", "thiên nhiên": "nature"}


def suggest_keyword(text):
    for term in sorted(KEYWORDS, key=len, reverse=True):
        if term in text.casefold():
            return KEYWORDS[term]
    return " ".join(text.split()[:10])[:100]


def search_pixabay(query, frame, duration):
    import requests
    key = config().get("PIXABAY_API_KEY", "")
    if not key or "your_" in key:
        raise VideoError("Chưa có PIXABAY_API_KEY trong .env.")
    params = {"q": query[:100], "lang": "vi" if not query.isascii() else "en",
              "video_type": "all", "safesearch": "true", "per_page": 10}
    digest = hashlib.sha256((key + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    cache = ROOT / "temp" / "pixabay-cache" / (digest + ".json")
    if cache.exists() and time.time() - cache.stat().st_mtime < 86400:
        data = load_json(cache)
    else:
        data = None
        for attempt in range(3):
            try:
                response = requests.get("https://pixabay.com/api/videos/", params={"key": key, **params}, timeout=25)
            except requests.RequestException:
                raise VideoError("Không kết nối được Pixabay; kiểm tra mạng. Khóa không được in ra log.") from None
            if response.status_code == 429:
                if attempt == 2:
                    raise VideoError("Pixabay giới hạn lượt gọi (429). Dừng tìm; dùng kết quả cache hoặc thử lại sau.")
                raw_wait = response.headers.get("X-RateLimit-Reset", "5")
                wait = min(15, max(2, int(raw_wait) if raw_wait.isdigit() else 5))
                time.sleep(wait)
                continue
            if response.status_code in (400, 401, 403):
                raise VideoError(f"Pixabay từ chối yêu cầu ({response.status_code}); kiểm tra khóa và tham số.")
            if response.status_code != 200:
                raise VideoError(f"Pixabay lỗi HTTP {response.status_code}.")
            data = response.json()
            save_json(cache, data)
            break
        if data is None:
            raise VideoError("Pixabay không trả về dữ liệu.")
    options = []
    for hit in data.get("hits", []):
        variants = [v for v in hit.get("videos", {}).values() if v.get("url") and min(v.get("width", 0), v.get("height", 0)) >= 720]
        if not variants:
            continue
        preferred = [v for v in variants if min(v["width"], v["height"]) >= 1080]
        video = min(preferred or variants, key=lambda v: v.get("size", 1e18))
        correct = video["height"] > video["width"] if frame == "9:16" else video["width"] >= video["height"]
        options.append({"pixabay_id": hit["id"], "page_url": hit["pageURL"], "user": hit.get("user", ""),
                        "tags": hit.get("tags", ""), "url": video["url"], "width": video["width"], "height": video["height"],
                        "duration": hit["duration"], "orientation_match": correct,
                        "needs_loop": hit["duration"] < duration})
    return sorted(options, key=lambda v: (not v["orientation_match"], v["needs_loop"]))[:3]


def plan_broll(job, retry=False):
    plan = load_json(job / "canh.json")
    if len(plan["scenes"]) > 20:
        raise VideoError("Mỗi lượt chỉ tìm tối đa 20 cảnh. Chia dự án hoặc chọn các cảnh cần minh họa.")
    for scene in plan["scenes"]:
        if scene.get("selected") or (scene.get("candidates") and not retry):
            continue
        keyword = scene.get("keyword") or suggest_keyword(scene["text"])
        scene["keyword"] = keyword
        try:
            scene["candidates"] = search_pixabay(keyword, plan["frame"], scene["end"] - scene["start"])
            scene.pop("error", None)
        except VideoError as error:
            scene["error"] = str(error)
            save_json(job / "canh.json", plan)
            write_review(job, plan)
            raise
        save_json(job / "canh.json", plan)
    plan["approved"] = False
    save_json(job / "canh.json", plan)
    write_review(job, plan)


def write_review(job, plan):
    lines = ["# [?] Duyệt cảnh minh họa", "", "Sửa `canh.json`: đặt `selected` bằng đối tượng trong `candidates`, hoặc `{\"file\": \"đường dẫn file cục bộ\"}`. Để `null` nếu giữ hình gốc/nền màu.", "", "| Cảnh | Giây | Nội dung | Đề xuất |", "|---|---|---|---|"]
    for s in plan["scenes"]:
        refs = [f"[{v['pixabay_id']}]({v['page_url']})" for v in s.get("candidates", [])]
        refs = " · ".join(refs) or s.get("error", "chưa tìm / dùng cảnh cục bộ")
        text = s["text"].replace("|", " ").replace("\n", " ")
        lines.append(f"| {s['id']} | {s['start']:.2f}–{s['end']:.2f} | {text} | {refs} |")
    (job / "duyet-canh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def download_selected(scene, job):
    chosen = scene.get("selected")
    if not chosen:
        return None
    if "file" in chosen:
        p = Path(chosen["file"]).expanduser().resolve()
        if not p.is_file():
            raise VideoError(f"Không có cảnh cục bộ: {p}")
        return p
    import requests
    url = chosen.get("url", "")
    if not url.startswith("https://cdn.pixabay.com/"):
        raise VideoError("URL tải cảnh phải là CDN chính thức Pixabay; dùng 'file' cho cảnh cục bộ.")
    p = ROOT / "temp" / "pixabay-downloads" / (hashlib.sha256(url.encode()).hexdigest() + ".mp4")
    if p.exists():
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    partial = p.with_suffix(".part")
    try:
        with requests.get(url, stream=True, timeout=45) as response:
            if response.status_code != 200:
                raise VideoError(f"Tải cảnh thất bại: HTTP {response.status_code}.")
            with partial.open("wb") as out:
                size = 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 500 * 1024 * 1024:
                        raise VideoError("Cảnh vượt 500 MB; chọn phiên bản nhỏ hơn.")
                    out.write(chunk)
        probe(partial)
        partial.replace(p)
    except requests.RequestException:
        raise VideoError("Lỗi mạng khi tải cảnh Pixabay.") from None
    finally:
        partial.unlink(missing_ok=True)
    return p


def groq_transcribe(audio, job, duration):
    import requests
    key = config().get("GROQ_API_KEY", "")
    if not key or "your_" in key:
        raise VideoError("Chưa có GROQ_API_KEY trong .env.")
    words, segments = [], []
    for index, start in enumerate(range(0, math.ceil(duration), 600)):
        chunk = job / f"groq-{index}.flac"
        run([tool("ffmpeg"), "-v", "error", "-y", "-ss", start, "-i", audio, "-t", min(601, duration - start),
             "-vn", "-ac", 1, "-ar", 16000, "-c:a", "flac", chunk])
        if chunk.stat().st_size > 25 * 1024 * 1024:
            raise VideoError("Đoạn audio vượt giới hạn 25 MB; cần chia nhỏ hơn.")
        with chunk.open("rb") as f:
            try:
                response = requests.post("https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {key}"}, files={"file": (chunk.name, f, "audio/flac")},
                    data=[("model", "whisper-large-v3-turbo"), ("language", "vi"), ("response_format", "verbose_json"),
                          ("timestamp_granularities[]", "word"), ("timestamp_granularities[]", "segment")], timeout=120)
            except requests.RequestException:
                raise VideoError("Lỗi mạng khi phiên âm Groq.") from None
        if response.status_code != 200:
            raise VideoError(f"Groq lỗi HTTP {response.status_code}; kiểm tra khóa, hạn mức hoặc thử lại sau.")
        data = response.json()
        boundary = min(duration, start + 600)
        for w in data.get("words", []):
            if start + float(w["start"]) >= boundary:
                continue
            words.append({"text": w["word"], "start": start + float(w["start"]), "end": min(boundary, start + float(w["end"]))})
        for s in data.get("segments", []):
            if start + float(s["start"]) < boundary:
                segments.append({"text": s["text"], "start": start + s["start"], "end": min(boundary, start + s["end"])})
    words.sort(key=lambda w: w["start"])
    if not words:
        raise VideoError("Groq không nhận được lời nói; kiểm tra đoạn video có tiếng người.")
    save_json(job / "transcript.json", {"words": words, "segments": segments, "model": "whisper-large-v3-turbo"})
    return words


def detect_cuts(audio, words, duration):
    log = run([tool("ffmpeg"), "-v", "info", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.6", "-f", "null", "-"]).stderr
    cuts, start = [], None
    for line in log.splitlines():
        begin = re.search(r"silence_start: ([\d.]+)", line)
        finish = re.search(r"silence_end: ([\d.]+)", line)
        if begin:
            start = float(begin[1])
        if finish and start is not None:
            end = min(duration, float(finish[1]))
            lo, hi = max(0, start + .12), max(0, end - .12)
            if hi - lo >= .35:
                cuts.append({"start": lo, "end": hi, "reason": "khoảng lặng", "enabled": True})
            start = None
    for w in words:
        if normalize(w["text"]) in {"ờ", "ừm", "uh", "um"} and w["end"] - w["start"] >= .08:
            cuts.append({"start": w["start"], "end": w["end"], "reason": "từ đệm: " + w["text"], "enabled": True})
    return {"approved": False, "duration": duration, "cuts": sorted(cuts, key=lambda c: c["start"]),
            "note": "[?] Xem lại điểm cắt. Không tự loại 'à', 'ừ' vì có thể mang nghĩa trong câu."}


def keep_ranges(cut_plan, duration):
    intervals = []
    for c in cut_plan.get("cuts", []):
        if c.get("enabled", True):
            a, b = max(0, float(c["start"])), min(duration, float(c["end"]))
            if not math.isfinite(a + b) or a >= b:
                raise VideoError("Điểm cắt không hợp lệ.")
            intervals.append((a, b))
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    keep, last = [], 0
    for a, b in merged:
        if a > last + .001:
            keep.append((last, a))
        last = b
    if last < duration - .001:
        keep.append((last, duration))
    if not keep:
        raise VideoError("Điểm cắt loại toàn bộ video.")
    return keep


def remap_words(words, keep):
    result, offset = [], 0
    for a, b in keep:
        for w in words:
            midpoint = (w["start"] + w["end"]) / 2
            if a <= midpoint < b:
                result.append({"text": w["text"], "start": offset + max(a, w["start"]) - a,
                               "end": offset + min(b, w["end"]) - a})
        offset += b - a
    return result


def frame_size(frame, width, source=None):
    width = width // 2 * 2
    if frame == "goc" and source:
        w = min(width, source["width"])
        h = round(w * source["height"] / source["width"]) // 2 * 2
        return w // 2 * 2, h
    return width, round(width * (16 / 9 if frame == "9:16" else 9 / 16)) // 2 * 2


def fit(width, height):
    return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,fps={FPS}"


def filter_path(path):
    return str(Path(path).resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "'\\\\''")


def render(job, args):
    meta = load_json(job / "job.json")
    plan = load_json(job / "canh.json")
    if any(s.get("selected") for s in plan["scenes"]) and not (plan.get("approved") or args.duyet):
        raise VideoError("Cảnh chưa được duyệt. Xem duyet-canh.md, chọn selected rồi dùng --duyet.")
    if args.duyet:
        plan["approved"] = True
        save_json(job / "canh.json", plan)
    source = Path(meta["source"]) if meta["mode"] == "edit" else None
    source_info = probe(source) if source else None
    width, height = frame_size(meta["frame"], args.rong, source_info["video"] if source else None)
    words = meta["words"]
    filters, inputs = [], []
    if source:
        cuts = load_json(job / "diem-cat.json")
        if not (cuts.get("approved") or args.duyet_cat):
            raise VideoError("Điểm cắt chưa được duyệt. Xem diem-cat.json rồi dùng --duyet-cat.")
        if args.duyet_cat:
            cuts["approved"] = True
            save_json(job / "diem-cat.json", cuts)
        keep = keep_ranges(cuts, meta["duration"])
        words = remap_words(words, keep)
        duration = sum(b - a for a, b in keep)
        inputs += ["-i", str(source)]
        n = len(keep)
        if n > 200:
            raise VideoError("Quá 200 đoạn cắt trong một lượt; chia video thành phần nhỏ hơn.")
        if n == 1:
            a, b = keep[0]
            filters += [f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,{fit(width,height)}[vbase]",
                        f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[abase]"]
        else:
            filters += [f"[0:v]split={n}" + "".join(f"[vs{i}]" for i in range(n)),
                        f"[0:a]asplit={n}" + "".join(f"[as{i}]" for i in range(n))]
            for i, (a, b) in enumerate(keep):
                d = b-a
                fade = min(.02, d/4)
                filters += [f"[vs{i}]trim=start={a}:end={b},setpts=PTS-STARTPTS,{fit(width,height)}[v{i}]",
                            f"[as{i}]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d={fade},afade=t=out:st={d-fade}:d={fade}[a{i}]"]
            filters.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vbase][abase]")
        # Scene intervals are always on the edited timeline. A changed cut plan invalidates earlier B-roll approvals.
        if meta.get("edited_duration") is None and any(s.get("selected") for s in plan["scenes"]):
            raise VideoError("Hãy chạy chuan-bi-canh sau khi duyệt điểm cắt để căn B-roll theo video đã sửa.")
        if meta.get("edited_duration") is not None and (abs(meta["edited_duration"] - duration) > .001 or meta.get("edited_keep") != [list(pair) for pair in keep]):
            raise VideoError("Điểm cắt đã đổi; chạy chuan-bi-canh lại trước khi chèn B-roll.")
        next_input = 1
    else:
        duration = meta["duration"]
        inputs += ["-f", "lavfi", "-i", f"color=c=0x15243a:s={width}x{height}:r={FPS}:d={duration}",
                   "-i", str(job / "giong-doc.mp3")]
        filters += ["[0:v]setpts=PTS-STARTPTS[vbase]", "[1:a]asetpts=PTS-STARTPTS[abase]"]
        next_input = 2
    vlabel = "vbase"
    sources = []
    for s in plan["scenes"]:
        selected = s.get("selected") or {}
        if selected.get("files"):
            paths = [Path(p).expanduser().resolve() for p in selected["files"]]
            if not 2 <= len(paths) <= 4 or not all(p.is_file() for p in paths):
                raise VideoError("Collage cần 2–4 file ảnh/video cục bộ có thật.")
            start, end = max(0, float(s["start"])), min(duration, float(s["end"]))
            if not math.isfinite(start + end) or end <= start:
                raise VideoError("Mốc collage không hợp lệ.")
            rows = 1 if len(paths) == 2 else 2
            cell_w, cell_h = (width // 4) * 2, (height // (rows * 2)) * 2
            labels = []
            for path in paths:
                index = next_input
                next_input += 1
                if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}:
                    inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(path)]
                else:
                    inputs += ["-stream_loop", "-1", "-i", str(path)]
                label = f"panel{index}"
                filters.append(f"[{index}:v]{fit(cell_w,cell_h)},trim=duration={end-start},setpts=PTS-STARTPTS[{label}]")
                labels.append(f"[{label}]")
            layout = "|".join(("0_0", "w0_0", "0_h0", "w0_h0")[:len(paths)])
            out = f"collage{next_input}"
            filters.append("".join(labels) + f"xstack=inputs={len(paths)}:layout={layout}:fill=black,{fit(width,height)},setpts=PTS-STARTPTS+{start}/TB[{out}]")
            merged = f"vcol{next_input}"
            filters.append(f"[{vlabel}][{out}]overlay=enable='gte(t,{start})*lt(t,{end})':eof_action=pass:repeatlast=0[{merged}]")
            vlabel = merged
            sources.append({"scene": s["id"], "start": start, "end": end, "selected": selected, "files": list(map(str,paths))})
            continue
        path = download_selected(s, job)
        if not path:
            continue
        start, end = max(0, float(s["start"])), min(duration, float(s["end"]))
        if end <= start:
            raise VideoError("Mốc B-roll không hợp lệ.")
        index = next_input
        next_input += 1
        if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}:
            inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(path)]
            chain = fit(width, height) + f",zoompan=z='min(pzoom+0.0005,1.06)':d=1:s={width}x{height}:fps={FPS}"
        else:
            inputs += ["-stream_loop", "-1", "-i", str(path)]
            chain = fit(width, height)
        filters.append(f"[{index}:v]{chain},trim=duration={end-start},setpts=PTS-STARTPTS+{start}/TB[br{index}]")
        out = f"vbr{index}"
        filters.append(f"[{vlabel}][br{index}]overlay=enable='gte(t,{start})*lt(t,{end})':eof_action=pass:repeatlast=0[{out}]")
        vlabel = out
        sources.append({"scene": s["id"], "start": start, "end": end, "selected": s["selected"], "file": str(path)})
    groups = write_captions(job, words, duration, width, height, args.kieu_chu)
    fontdir = ROOT / "skills" / "tao-kieu-chu-caption" / "fonts"
    filters.append(f"[{vlabel}]subtitles=filename='{filter_path(job/'phu-de.ass')}':fontsdir='{filter_path(fontdir)}',format=yuv420p[vout]")
    alabel = "abase"
    if args.nhac:
        music = Path(args.nhac).expanduser().resolve()
        if not music.is_file():
            raise VideoError("Không tìm thấy file nhạc.")
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        filters += ["[abase]asplit=2[adry][aside]", f"[{next_input}:a]volume=0.10,afade=t=in:d=0.6,afade=t=out:st={max(0,duration-1)}:d=1[music]",
                    "[music][aside]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[duck]",
                    "[adry][duck]amix=inputs=2:duration=first:normalize=0[amusic]"]
        alabel = "amusic"
        next_input += 1
    if args.sfx:
        sounds = load_json(args.sfx)
        labels = [f"[{alabel}]"]
        for i, sound in enumerate(sounds):
            path = Path(sound["file"]).expanduser().resolve()
            at = float(sound["at"])
            volume = float(sound.get("volume", .25))
            if not path.is_file() or not 0 <= at < duration or not 0 <= volume <= 1:
                raise VideoError("SFX có file, thời điểm hoặc âm lượng không hợp lệ.")
            inputs += ["-i", str(path)]
            filters.append(f"[{next_input}:a]volume={volume},adelay={round(at*1000)}:all=1[sfx{i}]")
            labels.append(f"[sfx{i}]")
            next_input += 1
        filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0[asfx]")
        alabel = "asfx"
    filters.append(f"[{alabel}]alimiter=limit=0.95[aout]")
    final = Path(args.output).expanduser().resolve() if args.output else job / "video-thanh-pham.mp4"
    if final.exists():
        raise VideoError("File đầu ra đã tồn tại. Chọn --output khác để giữ bản cũ.")
    if source and final == source:
        raise VideoError("Đầu ra phải khác file gốc.")
    final.parent.mkdir(parents=True, exist_ok=True)
    partial = final.with_name(final.stem + ".part.mp4")
    graph = job / "render.ffgraph"
    graph.write_text(";\n".join(filters), encoding="utf-8")
    version = run([tool("ffmpeg"), "-version"]).stdout
    major = re.search(r"ffmpeg version (\d+)", version)
    graph_option = "-/filter_complex" if not major or int(major[1]) >= 7 else "-filter_complex_script"
    cmd = [tool("ffmpeg"), "-v", "error", "-y", *inputs, "-filter_complex_threads", "1",
           graph_option, str(graph), "-map", "[vout]", "-map", "[aout]", "-t", f"{duration:.6f}",
           "-c:v", "libx264", "-crf", str(args.crf), "-preset", args.preset, "-threads", "4",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(partial)]
    print("Đang dựng video…", flush=True)
    run(cmd)
    info = probe(partial)
    video_end = float(info["video"].get("duration", info["duration"]))
    audio_end = float(info["audio"].get("duration", info["duration"])) if info["audio"] else 0
    last_caption = groups[-1]["end"] if groups else 0
    if abs(video_end - duration) > .15 or audio_end < duration - .15 or last_caption > video_end + .05:
        raise VideoError(f"Kiểm tra thời gian chưa đạt: video={video_end:.3f}, audio={audio_end:.3f}, dự kiến={duration:.3f}.")
    partial.replace(final)
    report = {"output": str(final), "expected_duration": duration, "measured_duration": info["duration"],
              "video_duration": video_end, "audio_duration": audio_end, "last_caption_end": last_caption,
              "size_mb": round(info["size"]/1048576, 2), "width": width, "height": height,
              "caption_groups": len(groups), "broll_count": len(sources), "sources": sources,
              "quality": "CRF là nén có mất dữ liệu; xem lại hình, tiếng và nội dung trước khi sử dụng."}
    save_json(job / "ket-qua.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def prepare_create(args):
    text = Path(args.kich_ban).read_text(encoding="utf-8-sig").strip()
    if not text:
        raise VideoError("Kịch bản trống.")
    job = make_job("tao")
    words, duration = asyncio.run(tts(text, job, args.giong))
    save_json(job / "job.json", {"mode": "create", "frame": args.khung, "duration": duration, "words": words, "script": text})
    plan = {"approved": False, "frame": args.khung, "duration": duration, "scenes": build_scenes(words, duration)}
    save_json(job / "canh.json", plan)
    write_review(job, plan)
    width, height = frame_size(args.khung, args.rong)
    write_captions(job, words, duration, width, height, args.kieu_chu)
    print(f"Đã chuẩn bị giọng đọc, phụ đề và cảnh: {job}", flush=True)
    if args.pixabay:
        plan_broll(job)
    print("Duyệt canh.json rồi chạy: autovideo.py xuat --job <thư mục trên> --duyet")


def prepare_edit(args):
    source = Path(args.video).expanduser().resolve()
    info = probe(source)
    if not info["video"] or not info["audio"]:
        raise VideoError("Video cần có cả hình và tiếng.")
    if args.tu < 0 or args.tu >= info["duration"]:
        raise VideoError("Mốc bắt đầu ngoài video.")
    duration = min(args.do_dai or info["duration"], info["duration"] - args.tu)
    job = make_job("sua")
    # A sample copy is only made when a time range is explicitly requested; original is never overwritten.
    if args.tu or args.do_dai:
        sample = job / "video-mau.mkv"
        run([tool("ffmpeg"), "-v", "error", "-y", "-ss", args.tu, "-i", source, "-t", duration,
             "-map", "0:v:0", "-map", "0:a:0", "-c:v", "ffv1", "-c:a", "pcm_s16le", sample])
        source = sample
        duration = probe(source)["duration"]
    audio = job / "audio.flac"
    run([tool("ffmpeg"), "-v", "error", "-y", "-i", source, "-vn", "-ac", 1, "-ar", 16000, "-c:a", "flac", audio])
    words = groq_transcribe(audio, job, duration)
    cuts = detect_cuts(audio, words, duration)
    save_json(job / "diem-cat.json", cuts)
    save_json(job / "job.json", {"mode": "edit", "source": str(source), "original": str(Path(args.video).resolve()),
              "sample_start": args.tu, "frame": args.khung, "duration": duration, "words": words})
    plan = {"approved": False, "frame": args.khung, "duration": duration, "scenes": []}
    save_json(job / "canh.json", plan)
    width, height = frame_size(args.khung, args.rong, info["video"])
    write_captions(job, words, duration, width, height, args.kieu_chu)
    print(f"Đã phiên âm {len(words)} từ, đề xuất {len(cuts['cuts'])} điểm cắt: {job}")
    print("Xem diem-cat.json và transcript.json trước khi xuất với --duyet-cat.")


def prepare_edit_scenes(job):
    meta = load_json(job / "job.json")
    if meta["mode"] != "edit":
        raise VideoError("Lệnh này dành cho video đang sửa.")
    cuts = load_json(job / "diem-cat.json")
    if not cuts.get("approved"):
        raise VideoError("Đặt approved=true trong diem-cat.json sau khi xem lại điểm cắt.")
    keep = keep_ranges(cuts, meta["duration"])
    duration = sum(b-a for a,b in keep)
    words = remap_words(meta["words"], keep)
    meta["edited_duration"] = duration
    meta["edited_keep"] = [list(pair) for pair in keep]
    save_json(job / "job.json", meta)
    plan = {"approved": False, "frame": meta["frame"], "duration": duration, "scenes": build_scenes(words, duration)}
    save_json(job / "canh.json", plan)
    write_review(job, plan)
    print(f"Cảnh đã căn theo video sau cắt: {job / 'canh.json'}")


def doctor():
    result = {"root": str(ROOT), "python": sys.version.split()[0]}
    errors = []
    for name in ("ffmpeg", "ffprobe"):
        try:
            result[name] = tool(name)
            run([result[name], "-version"])
        except (VideoError, OSError) as error:
            errors.append(clean_error(error))
    for module in ("edge_tts", "requests"):
        if importlib.util.find_spec(module) is None:
            errors.append(f"Thiếu thư viện {module}")
    result["keys"] = {key: "đã điền" if config().get(key) and "your_" not in config()[key] else "chưa điền"
                      for key in ("GROQ_API_KEY", "PIXABAY_API_KEY")}
    result["errors"] = errors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise VideoError("Môi trường chưa đủ; chạy bộ cài và kiểm tra lại.")


def compress(args):
    source, target = Path(args.video).resolve(), Path(args.output).resolve()
    if source == target or target.exists():
        raise VideoError("Chọn đầu ra mới, khác file gốc.")
    info = probe(source)
    if not info["video"]:
        raise VideoError("File đầu vào không có hình video.")
    target.parent.mkdir(parents=True, exist_ok=True)
    run([tool("ffmpeg"), "-v", "error", "-n", "-i", source, "-map", "0:v:0", "-map", "0:a?",
         "-c:v", "libx264", "-crf", args.crf, "-preset", args.preset, "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", target])
    result = probe(target)
    print(json.dumps({"output": str(target), "duration": result["duration"],
                      "size_mb": round(result["size"]/1048576, 2),
                      "reduction_percent": round((1-result["size"]/info["size"])*100, 1)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="autovideo-master — tạo, sửa, duyệt và xuất video")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("tao", help="Chuẩn bị video từ file kịch bản .txt")
    create.add_argument("--kich-ban", required=True)
    create.add_argument("--giong", default="vi-VN-HoaiMyNeural")
    create.add_argument("--khung", choices=("9:16", "16:9"), default="9:16")
    create.add_argument("--pixabay", action="store_true")
    edit = sub.add_parser("sua", help="Phiên âm và đề xuất điểm cắt video")
    edit.add_argument("--video", required=True)
    edit.add_argument("--tu", type=float, default=0)
    edit.add_argument("--do-dai", type=float)
    edit.add_argument("--khung", choices=("goc", "9:16", "16:9"), default="goc")
    export = sub.add_parser("xuat", help="Xuất một công việc đã chuẩn bị")
    export.add_argument("--job", required=True)
    export.add_argument("--duyet", action="store_true", help="Đã xem và đồng ý các cảnh selected")
    export.add_argument("--duyet-cat", action="store_true", help="Đã xem và đồng ý điểm cắt")
    export.add_argument("--output")
    export.add_argument("--nhac", help="File nhạc người dùng có quyền dùng")
    export.add_argument("--sfx", help="JSON các hiệu ứng [{file,at,volume}]")
    export.add_argument("--crf", type=int, choices=range(0, 52), default=20)
    export.add_argument("--preset", choices=("veryfast", "fast", "medium", "slow"), default="medium")
    for p in (create, edit, export):
        p.add_argument("--rong", type=int, default=1080)
        p.add_argument("--kieu-chu", choices=("vang-den", "trang-den", "toi-gian", "nen-den", "karaoke", "shorts"), default="vang-den")
    broll = sub.add_parser("broll", help="Tìm 3 cảnh đề xuất mỗi đoạn, chưa tải video")
    broll.add_argument("--job", required=True)
    broll.add_argument("--tim-lai", action="store_true")
    scenes = sub.add_parser("chuan-bi-canh", help="Căn B-roll theo video đã duyệt điểm cắt")
    scenes.add_argument("--job", required=True)
    sub.add_parser("kiem-tra", help="Kiểm tra công cụ và trạng thái khóa, không in khóa")
    compact = sub.add_parser("nen", help="Nén một video có sẵn; không dùng lại sau xuat")
    compact.add_argument("--video", required=True)
    compact.add_argument("--output", required=True)
    compact.add_argument("--crf", type=int, choices=range(0, 52), default=20)
    compact.add_argument("--preset", choices=("veryfast", "fast", "medium", "slow"), default="medium")
    args = parser.parse_args()
    if getattr(args, "rong", 1080) < 240 or getattr(args, "rong", 1080) > 3840:
        raise VideoError("Chiều rộng phải từ 240 đến 3840.")
    if getattr(args, "do_dai", None) is not None and args.do_dai <= 0:
        raise VideoError("Độ dài đoạn thử phải lớn hơn 0.")
    if args.command == "tao":
        prepare_create(args)
    elif args.command == "sua":
        prepare_edit(args)
    elif args.command == "xuat":
        render(Path(args.job).resolve(), args)
    elif args.command == "broll":
        plan_broll(Path(args.job).resolve(), args.tim_lai)
    elif args.command == "chuan-bi-canh":
        prepare_edit_scenes(Path(args.job).resolve())
    elif args.command == "nen":
        compress(args)
    else:
        doctor()


if __name__ == "__main__":
    try:
        main()
    except (VideoError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print("LỖI: " + clean_error(exc), file=sys.stderr)
        sys.exit(1)
