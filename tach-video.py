#!/usr/bin/env python3
"""Prepare, review and batch-export lessons from a recorded class."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
from types import SimpleNamespace
import unicodedata
import sys

import autovideo as av


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_identity(path):
    stat = path.stat()
    return {"path": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def checksum(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def slug(text):
    text = unicodedata.normalize("NFKD", text.casefold().replace("đ", "d")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:65] or "bai-hoc"


def seconds(value):
    if isinstance(value, str) and ":" in value:
        parts = value.split(":")
        if len(parts) not in (2, 3):
            raise av.VideoError("Mốc thời gian dùng giây hoặc HH:MM:SS.")
        numbers = list(map(float, parts))
        if any(n < 0 or not math.isfinite(n) for n in numbers) or any(n >= 60 for n in numbers[1:]):
            raise av.VideoError("Mốc HH:MM:SS không hợp lệ.")
        value = sum(n * 60 ** i for i, n in enumerate(reversed(numbers)))
    result = float(value)
    if not math.isfinite(result):
        raise av.VideoError("Mốc thời gian phải là số hữu hạn.")
    return result


def plan_videos(plan):
    """Flatten videos for rendering; keep their lesson and activity associations."""
    groups = plan.get("lessons", [])
    if not isinstance(groups, list) or not groups:
        raise av.VideoError("Chưa có bài trong bảng.")
    result, group_ids, block_ids = [], set(), set()
    for group_number, group in enumerate(groups, 1):
        if "blocks" not in group:
            result.append(group)
            continue
        key, title = str(group.get("id", "")), str(group.get("title", "")).strip()
        if not re.fullmatch(r"[a-zA-Z0-9-]{1,40}", key) or key in group_ids or not title:
            raise av.VideoError("Bài học cần id duy nhất và tiêu đề.")
        group_ids.add(key)
        blocks = group["blocks"]
        if not isinstance(blocks, list) or not blocks:
            raise av.VideoError("Bài học cần danh sách video/hoạt động có thứ tự.")
        last, number = None, 0
        for block in blocks:
            bid = str(block.get("id", ""))
            if not re.fullmatch(r"[a-zA-Z0-9-]{1,40}", bid) or bid in block_ids:
                raise av.VideoError("Mỗi video/hoạt động cần id duy nhất.")
            block_ids.add(bid)
            if block.get("type") == "video":
                number += 1
                last = {**block, "lesson_id": key, "lesson_title": title, "lesson_number": group_number,
                        "part_number": number, "activities_after": []}
                result.append(last)
            elif block.get("type") == "activity":
                if not str(block.get("instructions", "")).strip():
                    raise av.VideoError("Hoạt động cần hướng dẫn cho học viên.")
                duration = block.get("duration_minutes")
                if duration is not None and seconds(duration) <= 0:
                    raise av.VideoError("Thời gian thực hành phải lớn hơn 0 hoặc null.")
                if last is None:
                    raise av.VideoError("Ghi chú giữa video phải nằm sau một video.")
                target = block.get("next_video")
                later = blocks[blocks.index(block)+1:]
                if target and not any(b.get("type") == "video" and b.get("id") == target for b in later):
                    raise av.VideoError("Video sau hoạt động phải tồn tại phía sau trong cùng bài.")
                last["activities_after"].append(block)
            else:
                raise av.VideoError("Khối nội dung dùng type video hoặc activity.")
        if not number:
            raise av.VideoError("Một bài học cần ít nhất một video.")
    return result


def validate_plan(plan, meta):
    lessons = plan_videos(plan)
    if not isinstance(lessons, list) or not lessons:
        raise av.VideoError("Chưa có bài. AI cần đọc lời giảng và điền lessons trong bai-hoc.json trước.")
    seen, all_ranges, result = set(), [], []
    for lesson in lessons:
        key, title = str(lesson.get("id", "")), str(lesson.get("title", "")).strip()
        if not re.fullmatch(r"[a-zA-Z0-9-]{1,40}", key) or key in seen or not title:
            raise av.VideoError("Mỗi bài cần id duy nhất (chữ/số/gạch ngang) và tiêu đề.")
        seen.add(key)
        ranges = []
        for part in lesson.get("segments", []):
            a, b = seconds(part["start"]), seconds(part["end"])
            if a < meta["start"] or b > meta["end"] + .001 or b - a < .2:
                raise av.VideoError(f"Bài {key}: đoạn ngoài phần đã phiên âm hoặc ngắn dưới 0.2 giây.")
            if ranges and a < ranges[-1][1]:
                raise av.VideoError(f"Bài {key}: đoạn chồng nhau hoặc sai thứ tự.")
            ranges.append((a, min(b, meta["end"])))
        if not ranges or len(ranges) > 100:
            raise av.VideoError(f"Bài {key}: cần 1–100 đoạn giữ lại.")
        for a, b in ranges:
            if not plan.get("allow_reuse", False) and any(a < d - .001 and b > c + .001 for c, d in all_ranges):
                raise av.VideoError("Hai bài dùng trùng đoạn. Nếu chủ ý dùng lại, đặt allow_reuse=true.")
            all_ranges.append((a, b))
        result.append({**lesson, "id": key, "title": title, "segments": [{"start": a, "end": b} for a, b in ranges]})
    return result


def plan_hash(lessons, plan):
    return digest({"lessons": lessons, "structure": plan.get("lessons", []), "allow_reuse": plan.get("allow_reuse", False)})


def check_source(meta):
    path = Path(meta["source"])
    if not path.is_file() or source_identity(path) != meta["source_identity"]:
        raise av.VideoError("Video nguồn đã đổi hoặc mất. Chuẩn bị công việc mới để tránh dùng sai mốc.")
    return path


def readable_transcript(job, meta, words):
    chunks = {}
    line_words, line_start, last = [], None, 0
    lines = []
    for word in words:
        if line_words and (len(line_words) >= 28 or word["start"] - last > 1.2):
            lines.append(f"[{av.stamp(line_start)} → {av.stamp(last)}] " + " ".join(line_words))
            line_words, line_start = [], None
        line_start = word["start"] if line_start is None else line_start
        line_words.append(word["text"])
        last = word["end"]
    if line_words:
        lines.append(f"[{av.stamp(line_start)} → {av.stamp(last)}] " + " ".join(line_words))
    (job / "loi-giang.txt").write_text("\n".join(lines), encoding="utf-8")
    for word in words:
        i = int((word["start"] - meta["start"]) // 600)
        chunks.setdefault(i, []).append(word)
    directory = job / "loi-giang-tung-phan"
    directory.mkdir(exist_ok=True)
    for index, part in chunks.items():
        text = "\n".join(f"[{av.stamp(w['start'])}–{av.stamp(w['end'])}] {w['text']}" for w in part)
        (directory / f"phan-{index+1:02}.txt").write_text(text, encoding="utf-8")


def audit_repetition(job, meta):
    # Flag repetition for review, never silently remove or rewrite the source transcript.
    source=job / "transcript.json"
    if not source.exists():
        return
    groups={}
    for segment in av.load_json(source).get("segments",[]):
        text=" ".join(str(segment.get("text","")).casefold().split())
        if len(text)>=20:
            groups.setdefault(text,[]).append(segment)
    flagged=[]
    for text,segments in groups.items():
        if len(segments)>=4 and segments[-1]["start"]-segments[0]["start"]>=30:
            flagged.extend({"text":s["text"],"start":s["start"]+meta["start"],"end":s["end"]+meta["start"],
                            "reason":"Câu lặp nhiều lần; đối chiếu âm thanh, có thể là lỗi nhận dạng khi chờ/im lặng."} for s in segments)
    av.save_json(job / "can-kiem-tra-phien-am.json",sorted(flagged,key=lambda s:s["start"]))
    if flagged:
        print(f"Có {len(flagged)} mốc lặp cần kiểm tra; đã ghi can-kiem-tra-phien-am.json, chưa tự sửa phiên âm.")


def transcribe_course(job, imported=None):
    meta = av.load_json(job / "khoa-hoc.json")
    source = check_source(meta)
    if (job / "phien-am.json").exists():
        readable_transcript(job,meta,av.load_json(job / "phien-am.json")["words"])
        audit_repetition(job,meta)
        print("Đã có phiên âm; giữ bản đang có, tiếp tục lập/chỉnh bảng bài.")
        return
    if imported:
        raw_words = av.load_json(imported)["words"]
    else:
        audio = job / "audio.flac"
        if not audio.exists():
            av.run([av.tool("ffmpeg"), "-v", "error", "-y", "-ss", meta["start"], "-i", source,
                    "-t", meta["end"]-meta["start"], "-vn", "-ac", 1, "-ar", 16000, "-c:a", "flac", audio])
        raw_words = av.groq_transcribe(audio, job, meta["end"]-meta["start"])
    words = []
    for w in raw_words:
        a, b = seconds(w["start"]), seconds(w["end"])
        if a < 0 or b <= a or b > meta["end"]-meta["start"]+.15:
            raise av.VideoError("Phiên âm nhập có mốc ngoài phần video đã chọn.")
        words.append({"text": str(w.get("text", w.get("word", ""))), "start": a+meta["start"], "end": min(b+meta["start"], meta["end"])})
    if not words:
        raise av.VideoError("Không có lời giảng để chia bài.")
    words.sort(key=lambda w: w["start"])
    av.save_json(job / "phien-am.json", {"words": words, "time_base": "original_video_seconds", "imported": bool(imported)})
    readable_transcript(job, meta, words)
    audit_repetition(job,meta)
    print(f"Phiên âm đã sẵn: {len(words)} từ. AI đọc loi-giang.txt/từng phần, xem hình rồi lập bai-hoc.json.")


def prepare(args):
    source = Path(args.video).expanduser().resolve()
    info = av.probe(source)
    if not info["video"] or not info["audio"]:
        raise av.VideoError("Nguồn cần có hình và tiếng.")
    start = seconds(args.tu)
    end = min(info["duration"], start + seconds(args.do_dai)) if args.do_dai else info["duration"]
    if start < 0 or start >= end:
        raise av.VideoError("Khoảng chuẩn bị không hợp lệ.")
    if args.job:
        job = Path(args.job).expanduser().resolve()
        if job.exists() and any(job.iterdir()):
            raise av.VideoError("Thư mục đã có dữ liệu. Dùng tiep-tuc với công việc cũ.")
        job.mkdir(parents=True, exist_ok=True)
    else:
        job = av.make_job("khoa-hoc")
    av.save_json(job / "khoa-hoc.json", {"source": str(source), "source_identity": source_identity(source),
                "start": start, "end": end, "width": info["video"]["width"], "height": info["video"]["height"], "title": args.ten or source.stem})
    av.save_json(job / "bai-hoc.json", {"approved": False, "allow_reuse": False, "lessons": [],
                "note": "[?] AI đọc lời giảng rồi đề xuất chủ đề. Mốc start/end theo video gốc, không theo clip đã cắt."})
    (job / "huong-dan.md").write_text("Đọc loi-giang.txt và lập bai-hoc.json theo skills/tach-video-theo-noi-dung/SKILL.md.\nChạy xem-ke-hoach rồi chủ video duyệt trước xuat --duyet.\n", encoding="utf-8")
    print(f"Công việc: {job}", flush=True)
    transcribe_course(job, args.transcript)


def complement(ranges, start, end):
    cuts, previous = [], start
    for a, b in ranges:
        if a > previous+.001:
            cuts.append({"start": previous-start, "end": a-start, "enabled": True})
        previous = b
    if previous < end-.001:
        cuts.append({"start": previous-start, "end": end-start, "enabled": True})
    return cuts


def review(job, frames=True):
    meta, plan = av.load_json(job / "khoa-hoc.json"), av.load_json(job / "bai-hoc.json")
    source = check_source(meta)
    lessons = validate_plan(plan, meta)
    words = av.load_json(job / "phien-am.json")["words"]
    lines = [f"# Bảng chia bài: {meta['title']} [?]", "", "Mốc tính theo video gốc. Xem đủ ý trước khi duyệt.", ""]
    covered = []
    for i, lesson in enumerate(lessons, 1):
        duration = sum(s["end"]-s["start"] for s in lesson["segments"])
        if lesson.get("lesson_id") and lesson.get("part_number") == 1:
            lines += [f"## Bài {lesson['lesson_number']:02}: {lesson['lesson_title']}", ""]
        heading = f"### Video {lesson['part_number']}: {lesson['title']}" if lesson.get("lesson_id") else f"## {i:02}. {lesson['title']}"
        lines += [heading, f"ID video: {lesson['id']} · thời lượng giữ lại: {duration:.2f}s", str(lesson.get("summary", "")), ""]
        if lesson.get("learning_note"):
            lines += ["**Ghi chú dưới video:** " + str(lesson["learning_note"]), ""]
        for part in lesson["segments"]:
            a, b = part["start"], part["end"]
            covered.append((a,b))
            text = [w["text"] for w in words if a <= (w["start"]+w["end"])/2 < b]
            lines += [f"- {av.stamp(a)} → {av.stamp(b)}", "  - Đầu: " + " ".join(text[:20]), "  - Cuối: " + " ".join(text[-20:])]
        if frames:
            # Three boundary/interior images from retained content, not removed gaps.
            positions = [lesson["segments"][0]["start"]+.1, (lesson["segments"][0]["start"]+lesson["segments"][0]["end"])/2, lesson["segments"][-1]["end"]-.1]
            directory = job / "anh-duyet"
            directory.mkdir(exist_ok=True)
            for n, position in enumerate(positions):
                image = directory / f"{i:02}-{lesson['id']}-{n+1}.jpg"
                av.run([av.tool("ffmpeg"), "-v", "error", "-y", "-ss", position, "-i", source, "-frames:v", 1,
                        "-vf", "scale=960:-2", "-q:v", 3, image])
                if not image.is_file() or not image.stat().st_size:
                    raise av.VideoError("Không lấy được hình tại ranh giới bài; xem lại mốc.")
                lines.append(f"![Mốc {av.stamp(position)}](anh-duyet/{image.name})")
        for activity in lesson.get("activities_after", []):
            lines += ["", "**Ghi chú giữa các video trong cùng bài:** " + activity["instructions"],
                      "Vị trí: dưới video, trước phần tiếp theo; không gắn lên hình.", ""]
        lines.append("")
    # Merge coverage to list precisely the source material excluded by the proposal.
    merged = []
    for a,b in sorted(covered):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a,b))
    excluded = complement(merged,meta["start"],meta["end"])
    lines += ["## Các khoảng không đưa vào bài", ""]
    for c in excluded:
        lines.append(f"- {av.stamp(meta['start']+c['start'])} → {av.stamp(meta['start']+c['end'])}")
    if not excluded:
        lines.append("Giữ toàn bộ khoảng đã phiên âm.")
    flags=job / "can-kiem-tra-phien-am.json"
    if flags.exists():
        retained=[s for s in av.load_json(flags) if any(s["start"]<b and s["end"]>a for a,b in covered)]
        lines += ["", "## Mốc phiên âm cần đối chiếu trong phần giữ lại", ""]
        for item in retained:
            lines.append(f"- {av.stamp(item['start'])}: {item['text']} — {item['reason']}")
        if not retained:
            lines.append("Không có câu lặp đã đánh dấu trong các đoạn giữ lại. Chữ nhận sai khác vẫn cần kiểm tra.")
    fingerprint = plan_hash(lessons, plan)
    if plan.get("approved_hash") != fingerprint:
        plan["approved"] = False
        av.save_json(job / "bai-hoc.json", plan)
    (job / "duyet-bai-hoc.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(plan['lessons'])} bài / {len(lessons)} video; bảng duyệt: {job / 'duyet-bai-hoc.md'}")


def reusable(record, signature):
    path = Path(record.get("output", ""))
    return bool(record.get("status") == "done" and record.get("signature") == signature and path.is_file()
                and record.get("sha256") == checksum(path) and record.get("assets")
                and all(Path(p).is_file() and checksum(p) == h for p,h in record["assets"].items()))


def acquire_lock(job):
    handle=(job / "xuat.lock").open("a+b")
    if not handle.tell():
        handle.write(b"0");handle.flush()
    handle.seek(0)
    try:
        if os.name=="nt":
            import msvcrt
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise av.VideoError("Công việc này đang có lượt xuất khác chạy. Chờ lượt đó kết thúc.") from None
    return handle


def release_lock(handle):
    if os.name=="nt":
        import msvcrt
        handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(),fcntl.LOCK_UN)
    handle.close()


def catalogue(job, lessons, states, plan=None):
    entries = []
    for i, lesson in enumerate(lessons,1):
        record = states.get(lesson["id"], {})
        entries.append({"number": i, "id": lesson["id"], "title": lesson["title"], "summary": lesson.get("summary", ""),
                        "lesson_id": lesson.get("lesson_id", lesson["id"]), "lesson_title": lesson.get("lesson_title", lesson["title"]),
                        "part_number": lesson.get("part_number", 1), "activities_after": lesson.get("activities_after", []),
                        "learning_note": lesson.get("learning_note", ""), "practice": lesson.get("practice"),
                        "status": record.get("status", "pending"), "video": record.get("output", ""),
                        "duration": record.get("duration", ""), "subtitle": record.get("subtitle", ""), "thumbnail": record.get("thumbnail", "")})
    av.save_json(job / "danh-muc.json", entries)
    if plan and any("blocks" in group for group in plan["lessons"]):
        lookup = {item["id"]: item for item in entries}
        groups = []
        for group in plan["lessons"]:
            blocks = [({**block, **lookup[block["id"]]} if block.get("type") == "video" else block)
                      for block in group.get("blocks", [])]
            if "blocks" not in group:
                blocks = [{"type":"video", **lookup[group["id"]]}]
            groups.append({**group, "blocks": blocks})
        av.save_json(job / "cau-truc-bai-hoc.json", {"lessons": groups})
    with (job / "danh-muc.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(entries[0]))
        writer.writeheader();writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict,list)) else v for k,v in entry.items()} for entry in entries)
    text=["# Các bài đã xuất [?]", "", "Kiểm tra chữ, đầu/cuối câu và hình/tiếng trước khi dùng.", ""]
    for item in entries:
        if item["part_number"] == 1:
            text += [f"## {item['lesson_title']}", ""]
        text.append(f"Video {item['part_number']}: {item['title']} — {item['status']}")
        if item.get("learning_note"):
            text.append("   Ghi chú dưới video: " + item["learning_note"])
        if item["video"]:
            text.append(f"   [Video]({Path(item['video']).relative_to(job).as_posix()}) · {item['duration']}s")
        for activity in item["activities_after"]:
            text += ["", "Ghi chú trước video tiếp theo: " + activity["instructions"], ""]
    (job / "danh-muc.md").write_text("\n".join(text),encoding="utf-8")


def export(job, args):
    meta, plan = av.load_json(job / "khoa-hoc.json"), av.load_json(job / "bai-hoc.json")
    source = check_source(meta)
    lessons = validate_plan(plan,meta)
    approval = plan_hash(lessons,plan)
    if args.duyet:
        plan.update(approved=True,approved_hash=approval)
        av.save_json(job / "bai-hoc.json",plan)
    if not plan.get("approved") or plan.get("approved_hash") != approval:
        raise av.VideoError("Bảng bài chưa duyệt hoặc đã đổi. Xem lại duyet-bai-hoc.md rồi dùng --duyet.")
    words = av.load_json(job / "phien-am.json")["words"]
    state_path = job / "tien-do.json"
    states = av.load_json(state_path) if state_path.exists() else {}
    frame = args.khung or ("9:16" if args.muc_dich == "clip-ngan" else "goc")
    options = {"width": args.rong or (meta["width"] if frame == "goc" else 1080), "frame": frame,
               "purpose": args.muc_dich, "style": args.kieu_chu, "captions": args.phu_de,
               "crf": args.crf, "preset": args.preset, "engine": "course-v1"}
    failed=0
    handle=acquire_lock(job)
    try:
        for i, lesson in enumerate(lessons,1):
            ranges = [(s["start"],s["end"]) for s in lesson["segments"]]
            a,b=ranges[0][0],ranges[-1][1]
            selected=[w for w in words if a <= (w["start"]+w["end"])/2 < b]
            signature=digest({"source": meta["source_identity"], "lesson":lesson,"words":selected,"options":options})
            record=states.get(lesson["id"],{})
            if reusable(record,signature):
                print(f"{i}/{len(lessons)}: giữ bài đã kiểm tra {lesson['title']}",flush=True)
                continue
            base=job / "bai-da-xuat"
            if lesson.get("lesson_id"):
                base=base / f"{lesson['lesson_id']}-{slug(lesson['lesson_title'])}"
            directory=base / f"{lesson.get('part_number',i):02}-{slug(lesson['title'])}-{signature[:8]}"
            directory.mkdir(parents=True,exist_ok=True)
            target=directory / "video.mp4"
            # An interrupted unverified final is preserved separately, never trusted by existence alone.
            if target.exists():
                target=directory / f"video-chay-lai-{av.uuid.uuid4().hex[:6]}.mp4"
            record={"status":"running","signature":signature,"output":str(target)}
            states[lesson["id"]]=record;av.save_json(state_path,states)
            print(f"{i}/{len(lessons)}: xuất {lesson['title']}",flush=True)
            try:
                local_words=[{**w,"start":w["start"]-a,"end":w["end"]-a} for w in selected]
                av.save_json(directory / "job.json",{"mode":"edit","source":str(source),"source_start":a,
                            "duration":b-a,"frame":frame,"words":local_words})
                av.save_json(directory / "diem-cat.json",{"approved":True,"cuts":complement(ranges,a,b)})
                av.save_json(directory / "canh.json",{"approved":True,"scenes":[]})
                parameters=SimpleNamespace(duyet=False,duyet_cat=False,rong=options["width"],kieu_chu=args.kieu_chu,
                            nhac=None,sfx=None,output=str(target),crf=args.crf,preset=args.preset,phu_de_roi=args.phu_de=="roi")
                av.render(directory,parameters)
                image=directory / "anh-dai-dien.jpg"
                av.run([av.tool("ffmpeg"),"-v","error","-y","-ss",min(.5,(ranges[0][1]-a)/2),"-i",target,
                        "-frames:v",1,"-vf","scale=960:-2","-q:v",3,image])
                if not image.is_file() or not image.stat().st_size:
                    raise av.VideoError("Chưa tạo được ảnh đại diện; chưa đánh dấu bài hoàn tất.")
                result=av.load_json(directory / "ket-qua.json")
                record.update(status="done",sha256=checksum(target),duration=result["measured_duration"],
                              subtitle=str(directory / "phu-de.srt"),thumbnail=str(image))
                record["assets"]={str(p):checksum(p) for p in (directory / "phu-de.srt",directory / "phu-de.ass",image)}
                av.save_json(directory / "ghi-chu-bai-hoc.json", lesson)
                record["assets"][str(directory / "ghi-chu-bai-hoc.json")]=checksum(directory / "ghi-chu-bai-hoc.json")
                mapped=av.remap_words(local_words,[(x-a,y-a) for x,y in ranges])
                (directory / "noi-dung.txt").write_text(" ".join(w["text"] for w in mapped),encoding="utf-8")
                (directory / "bai-hoc.md").write_text(f"# {lesson['title']} [?]\n\n{lesson.get('summary','')}\n\nGhi chú dưới video: {lesson.get('learning_note','Không có bài thực hành riêng.')}\n\nNguồn: {source.name}\nCác đoạn gốc: {json.dumps(lesson['segments'],ensure_ascii=False)}\n",encoding="utf-8")
            except (av.VideoError,OSError,ValueError,KeyError) as exc:
                failed+=1;record.update(status="failed",error=av.clean_error(exc))
                print(f"Bài lỗi: {lesson['title']} — {record['error']}",file=sys.stderr)
            av.save_json(state_path,states);catalogue(job,lessons,states,plan)
        catalogue(job,lessons,states,plan)
    finally:
        release_lock(handle)
    if failed:
        raise av.VideoError(f"{failed} bài lỗi; các bài đạt đã giữ. Sửa lỗi rồi chạy lại cùng lệnh.")
    print(f"Đã xuất/kiểm tra {len(lessons)} video trong {len(plan['lessons'])} bài: {job / 'danh-muc.md'}")


def main():
    parser=argparse.ArgumentParser(description="Tạo các video bài học từ bản ghi; dùng AI để đề xuất nội dung.")
    sub=parser.add_subparsers(dest="command",required=True)
    prep=sub.add_parser("chuan-bi")
    prep.add_argument("--video",required=True);prep.add_argument("--tu",default="0");prep.add_argument("--do-dai")
    prep.add_argument("--job");prep.add_argument("--ten");prep.add_argument("--transcript",help="Phiên âm có sẵn, mốc tương đối trong phần đã chọn; không gọi API")
    resume=sub.add_parser("tiep-tuc");resume.add_argument("--job",required=True);resume.add_argument("--transcript")
    preview=sub.add_parser("xem-ke-hoach");preview.add_argument("--job",required=True);preview.add_argument("--khong-anh",action="store_true")
    batch=sub.add_parser("xuat");batch.add_argument("--job",required=True);batch.add_argument("--duyet",action="store_true")
    batch.add_argument("--muc-dich",choices=("bai-hoc","clip-ngan"),default="bai-hoc")
    batch.add_argument("--khung",choices=("goc","9:16","16:9"))
    batch.add_argument("--rong",type=int,default=0);batch.add_argument("--phu-de",choices=("roi","gan"),default="roi")
    batch.add_argument("--kieu-chu",choices=("vang-den","trang-den","toi-gian","nen-den","karaoke","shorts"),default="toi-gian")
    batch.add_argument("--crf",type=int,choices=range(0,52),default=20)
    batch.add_argument("--preset",choices=("veryfast","fast","medium","slow"),default="medium")
    args=parser.parse_args()
    if getattr(args,"rong",0) and not 240 <= args.rong <= 3840:
        raise av.VideoError("Chiều rộng phải từ 240 đến 3840, hoặc 0 để giữ kích thước nguồn.")
    if args.command=="chuan-bi":prepare(args)
    elif args.command=="tiep-tuc":transcribe_course(Path(args.job).resolve(),args.transcript)
    elif args.command=="xem-ke-hoach":review(Path(args.job).resolve(),not args.khong_anh)
    else:export(Path(args.job).resolve(),args)


if __name__=="__main__":
    try:main()
    except (av.VideoError,OSError,ValueError,KeyError) as error:
        print("LỖI: "+av.clean_error(error),file=sys.stderr);sys.exit(1)
