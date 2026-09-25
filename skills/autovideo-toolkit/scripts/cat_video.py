"""Cat bo cac doan da duyet ra khoi video, ghep lai thanh ban hoan chinh.

Nhan danh sach diem cat (tu tim_tu_dem.py, da loc nhung cho nguoi dung TICH CHON)
roi cat bo dung nhung cho do.

Lam dung luat cua bo cong cu:
  - Cat tung doan roi ghep KHONG ma hoa lai (-c copy) -> khong giam chat luong
  - Mo/tat tieng 30ms o moi bien -> khong "pop" tai cho noi
  - Chua dem 2 dau moi doan cat -> moc gio boc chu lech 50-100ms, dem se hut

Dung:
    python helpers/cat_video.py video.mp4 --diem-cat diem-cat.json -o ra.mp4
    python helpers/cat_video.py video.mp4 --diem-cat da-duyet.json -o ra.mp4 --dem 0.06
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

FADE = 0.03      # 30ms mo/tat tieng moi bien - chong tieng "pop"
DEM = 0.05       # 50ms chua dem 2 dau moi doan cat


def chay(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def do_dai(video: Path) -> float:
    r = chay(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=noprint_wrappers=1:nokey=1", str(video)])
    return float(r.stdout.strip())


def gop_chong_lan(khoang: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Gop cac khoang cat bi chong lan hoac dinh nhau."""
    if not khoang:
        return []
    khoang = sorted(khoang)
    ra = [list(khoang[0])]
    for bd, kt in khoang[1:]:
        if bd <= ra[-1][1] + 0.01:
            ra[-1][1] = max(ra[-1][1], kt)
        else:
            ra.append([bd, kt])
    return [(a, b) for a, b in ra]


def tinh_doan_giu(dai: float, cat: list[tuple[float, float]],
                  toi_thieu: float = 0.12) -> list[tuple[float, float]]:
    """Nghich dao danh sach cat -> danh sach doan GIU LAI."""
    giu: list[tuple[float, float]] = []
    hien = 0.0
    for bd, kt in cat:
        if bd - hien >= toi_thieu:
            giu.append((hien, bd))
        hien = max(hien, kt)
    if dai - hien >= toi_thieu:
        giu.append((hien, dai))
    return giu


def main() -> None:
    ap = argparse.ArgumentParser(description="Cat bo cac doan da duyet")
    ap.add_argument("video", type=Path)
    ap.add_argument("--diem-cat", type=Path, required=True,
                    help="File JSON danh sach cho CAN BO (bat_dau, ket_thuc)")
    ap.add_argument("-o", "--ra", type=Path, required=True)
    ap.add_argument("--dem", type=float, default=DEM,
                    help=f"Chua dem 2 dau moi doan cat, giay (mac dinh {DEM})")
    args = ap.parse_args()

    if not args.video.exists():
        sys.exit(f"Khong thay video: {args.video}")
    if not args.diem_cat.exists():
        sys.exit(f"Khong thay file diem cat: {args.diem_cat}")

    ds = json.loads(args.diem_cat.read_text(encoding="utf-8"))
    if isinstance(ds, dict):
        ds = ds.get("diem_cat", [])

    dai = do_dai(args.video)

    # chua dem 2 dau: cat HEP lai mot chut cho an toan
    cat = []
    for m in ds:
        bd = float(m["bat_dau"]) + args.dem
        kt = float(m["ket_thuc"]) - args.dem
        if kt - bd > 0.02:
            cat.append((max(0.0, bd), min(dai, kt)))

    cat = gop_chong_lan(cat)
    giu = tinh_doan_giu(dai, cat)

    if not giu:
        sys.exit("Cat het thi khong con gi. Xem lai danh sach diem cat.")

    tong_bo = sum(b - a for a, b in cat)
    print(f"Video goc  : {dai:.2f}s")
    print(f"Bo di      : {len(cat)} doan, {tong_bo:.2f}s ({tong_bo/dai*100:.0f}%)")
    print(f"Giu lai    : {len(giu)} doan, {dai - tong_bo:.2f}s")

    args.ra.parent.mkdir(parents=True, exist_ok=True)

    if not cat:
        print("Khong co gi de cat - chep nguyen video.")
        chay(["ffmpeg", "-v", "error", "-i", str(args.video), "-c", "copy",
              "-y", str(args.ra)])
        return

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        manh: list[Path] = []
        for i, (bd, kt) in enumerate(giu):
            f = t / f"m{i:04d}.mp4"
            do_dai_doan = kt - bd
            # mo/tat tieng 30ms moi bien -> khong pop khi noi
            loc_tieng = (f"afade=t=in:st=0:d={FADE},"
                         f"afade=t=out:st={max(0, do_dai_doan - FADE):.3f}:d={FADE}")
            r = chay([
                "ffmpeg", "-v", "error", "-ss", f"{bd:.3f}", "-i", str(args.video),
                "-t", f"{do_dai_doan:.3f}",
                "-af", loc_tieng,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                "-avoid_negative_ts", "make_zero",
                "-y", str(f),
            ])
            if f.exists() and f.stat().st_size > 0:
                manh.append(f)
            else:
                print(f"  (bo qua doan {i}: {r.stderr.strip()[:120]})")

        if not manh:
            sys.exit("Khong cat duoc doan nao")

        ds_file = t / "danh-sach.txt"
        ds_file.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in manh), encoding="utf-8")

        r = chay(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
                  "-i", str(ds_file), "-c", "copy", "-y", str(args.ra)])
        if not args.ra.exists():
            sys.exit(f"Ghep khong xong: {r.stderr[:300]}")

    moi = do_dai(args.ra)
    print(f"Xong       : {args.ra}  ({moi:.2f}s)")


if __name__ == "__main__":
    main()
