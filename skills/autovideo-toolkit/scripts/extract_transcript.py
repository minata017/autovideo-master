"""Trich transcript Scribe JSON -> 2 file text de doc:
  <stem>_full.txt     : text thuan
  <stem>_timeline.txt : theo moc thoi gian [mm:ss] (speaker) doan noi
"""
import json, sys
from pathlib import Path

src = Path(sys.argv[1])
data = json.loads(src.read_text(encoding="utf-8"))

full = data.get("text", "")
out_full = src.with_name(src.stem + "_full.txt")
out_full.write_text(full, encoding="utf-8")

def mmss(s):
    s = int(s or 0)
    return f"{s//60:02d}:{s%60:02d}"

words = data.get("words", [])
# Gom thanh doan: doi speaker HOAC qua ~25s thi xuong dong moi
lines = []
cur_spk = None
cur_start = None
buf = []
last_end = 0.0
GAP = 25.0

def flush():
    if buf:
        lines.append(f"[{mmss(cur_start)}] ({cur_spk}) " + "".join(buf).strip())

for w in words:
    if w.get("type") == "spacing":
        buf.append(w.get("text", " "))
        continue
    spk = w.get("speaker_id", "?")
    st = w.get("start", last_end)
    if cur_spk is None:
        cur_spk, cur_start = spk, st
    elif spk != cur_spk or (st - last_end) > GAP or (st - cur_start) > 25:
        flush()
        buf = []
        cur_spk, cur_start = spk, st
    buf.append(w.get("text", ""))
    last_end = w.get("end", st)
flush()

out_tl = src.with_name(src.stem + "_timeline.txt")
out_tl.write_text("\n".join(lines), encoding="utf-8")

# Thong ke
spk_time = {}
for w in words:
    if w.get("type") == "spacing":
        continue
    spk = w.get("speaker_id", "?")
    dur = (w.get("end", 0) or 0) - (w.get("start", 0) or 0)
    spk_time[spk] = spk_time.get(spk, 0) + dur

print(f"full chars: {len(full):,}")
print(f"timeline blocks: {len(lines):,}")
print(f"total words: {len(words):,}")
print("speakers (giay noi):")
for spk, t in sorted(spk_time.items(), key=lambda x: -x[1]):
    print(f"  {spk}: {t:.0f}s ({t/60:.1f} phut)")
print(f"OUT: {out_full.name} | {out_tl.name}")
