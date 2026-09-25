"""Cham chat luong video bang NGUONG SO - truoc khi giao cho nguoi xem.

Vi sao: truoc day kiem bang mat, moi lan moi kieu, va hay sot. Script nay do bang
may voi nguong cu the, moi loi deu noi ro SO DO va NGUONG BI VUOT.

Bay phep kiem:
  1. Duong tieng   - co tieng khong, am luong co qua nho/qua to khong
  2. Doan cam dai  - co doan nao khong ai noi qua lau khong
  3. Do dai        - co nam trong khoang hop voi loai video khong
  4. Khung hinh    - ti le va do phan giai
  5. Khung den     - dau va cuoi video co bi den khong (loi duoi den hay gap)
  6. Do sang       - khung co qua toi hoac chay sang khong
  7. Mo dau co nguoi - THO, do vung mau da. Tin cay THAP, xem bang mat de chac

Dung:
    python helpers/kiem_chat_luong.py video.mp4
    python helpers/kiem_chat_luong.py video.mp4 --loai reel
    python helpers/kiem_chat_luong.py video.mp4 --json bao-cao.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

# --- NGUONG (sua o day, dung rai rac trong ma) ---
NGUONG = {
    "am_luong_min_db": -35.0,      # trung binh duoi muc nay = tieng qua nho
    "am_luong_max_db": -8.0,       # tren muc nay = de vo tieng
    "dinh_toi_da_db": -0.5,        # dinh cham 0 = da bi vo
    "cam_dai_giay": 3.0,           # khong ai noi lien tuc qua lau
    "khung_den_nguong": 18,        # do sang trung binh duoi nay = coi nhu den
    "qua_toi": 45,                 # khung trung binh duoi nay = thieu sang
    "chay_sang": 215,              # tren nay = chay sang
    "da_toi_thieu_pct": 3.0,       # mo dau: vung mau da it hon nay = kha nang khong co nguoi
}

DO_DAI_THEO_LOAI = {
    "reel": (12, 95),
    "quang-cao": (15, 60),
    "bai-hoc": (60, 900),
    "phim": (30, 3600),
    "do-hoa": (3, 120),      # the chuong, chu chay, bieu do - KHONG co nguoi quay
}

# Video DO HOA thi nen toi la CHU Y (gu Xuong Video AI nen #0B0F1A),
# va khong co mat nguoi cung la binh thuong. Doi nguong cho loai nay.
# (Bai hoc 02/08: chay thu tren video do hoa nen toi, may bao "khung den" +
#  "hinh toi" + "khong co nguoi" - ca ba deu la BAO DONG GIA.)
LOAI_DO_HOA = {"do-hoa"}
NGUONG_DO_HOA = {
    "khung_den_nguong": 6,     # nen toi that su la #0B0F1A ~ do sang 13
    "qua_toi": 8,
}


def chay(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (r.stdout or "") + (r.stderr or "")


def doc_thong_so(video: Path) -> dict:
    out = chay([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video),
    ])
    return json.loads(out)


def do_am_luong(video: Path) -> dict | None:
    """Do am luong trung binh va dinh bang ffmpeg volumedetect."""
    out = chay(["ffmpeg", "-i", str(video), "-af", "volumedetect", "-f", "null", "-"])
    tb = dinh = None
    for dong in out.splitlines():
        if "mean_volume:" in dong:
            tb = float(dong.split("mean_volume:")[1].split("dB")[0].strip())
        if "max_volume:" in dong:
            dinh = float(dong.split("max_volume:")[1].split("dB")[0].strip())
    if tb is None:
        return None
    return {"trung_binh_db": tb, "dinh_db": dinh}


def trich_khung(video: Path, giay: float, dich: Path, rong: int = 320) -> bool:
    chay([
        "ffmpeg", "-v", "error", "-ss", str(giay), "-i", str(video),
        "-frames:v", "1", "-vf", f"scale={rong}:-1", "-y", str(dich),
    ])
    return dich.exists() and dich.stat().st_size > 0


def do_khung(duong_dan: Path) -> dict:
    """Do do sang trung binh va ti le vung mau da cua mot khung."""
    img = Image.open(duong_dan).convert("RGB")
    a = np.asarray(img).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    sang = float(a.mean())

    # Vung mau da: khoang mau da nguoi rong (nhieu tong da khac nhau).
    # THO - tuong mau be, go, cat cung lot luoi. Chi dung lam chi bao.
    da = (
        (r > 80) & (r < 255)
        & (g > 45) & (g < 220)
        & (b > 30) & (b < 200)
        & (r > g + 12) & (g > b - 5) & (r > b + 10)
    )
    return {"do_sang": round(sang, 1), "vung_da_pct": round(float(da.mean() * 100), 1)}


def kiem(video: Path, loai: str) -> list[dict]:
    loi: list[dict] = []

    # Video do hoa: nen toi va khong co mat nguoi deu la CHU Y, khong phai loi
    la_do_hoa = loai in LOAI_DO_HOA
    nguong = dict(NGUONG)
    if la_do_hoa:
        nguong.update(NGUONG_DO_HOA)

    def ghi(muc: str, ten: str, so_do: str, nguong: str, khuyen: str, tin_cay: str = "chac"):
        loi.append({
            "muc": muc, "phep_kiem": ten, "so_do": so_do,
            "nguong": nguong, "khuyen_nghi": khuyen, "tin_cay": tin_cay,
        })

    ts = doc_thong_so(video)
    v_streams = [s for s in ts["streams"] if s["codec_type"] == "video"]
    a_streams = [s for s in ts["streams"] if s["codec_type"] == "audio"]
    if not v_streams:
        ghi("LOI", "duong hinh", "khong co", "phai co 1", "File nay khong phai video")
        return loi

    vs = v_streams[0]
    w, h = int(vs["width"]), int(vs["height"])
    dai = float(ts["format"]["duration"])

    # --- 1. Duong tieng ---
    if not a_streams:
        ghi("LOI", "duong tieng", "khong co duong tieng", "phai co",
            "Video CAM. Kiem lai the <audio> co id chua, hai duong tieng co trung lop khong")
    else:
        am = do_am_luong(video)
        if am:
            tb, dinh = am["trung_binh_db"], am["dinh_db"]
            if tb < NGUONG["am_luong_min_db"]:
                ghi("LOI", "am luong", f"{tb:.1f} dB", f"phai tren {NGUONG['am_luong_min_db']} dB",
                    "Tieng qua nho, nguoi xem phai van loa. Tang am len")
            elif tb > NGUONG["am_luong_max_db"]:
                ghi("CANH BAO", "am luong", f"{tb:.1f} dB", f"nen duoi {NGUONG['am_luong_max_db']} dB",
                    "Tieng to qua, de rat tai")
            if dinh is not None and dinh > NGUONG["dinh_toi_da_db"]:
                ghi("CANH BAO", "dinh tieng", f"{dinh:.1f} dB", f"nen duoi {NGUONG['dinh_toi_da_db']} dB",
                    "Dinh cham tran, co the da vo tieng cho to nhat")

    # --- 2. Do dai ---
    if loai in DO_DAI_THEO_LOAI:
        lo, hi = DO_DAI_THEO_LOAI[loai]
        if dai < lo:
            ghi("CANH BAO", "do dai", f"{dai:.1f}s", f"{loai}: {lo}-{hi}s",
                "Ngan hon thuong le, xem lai co bi cat hut khong")
        elif dai > hi:
            ghi("CANH BAO", "do dai", f"{dai:.1f}s", f"{loai}: {lo}-{hi}s",
                "Dai hon thuong le, can nhac cat bot")

    # --- 3. Khung hinh ---
    ti_le = w / h
    ten_ti_le = "doc" if ti_le < 0.85 else ("vuong" if ti_le < 1.15 else "ngang")
    if min(w, h) < 720:
        ghi("CANH BAO", "do phan giai", f"{w}x{h}", "canh ngan nen tu 720 tro len",
            "Hinh se mem khi xem tren man to")
    if loai in ("reel", "quang-cao") and ten_ti_le == "ngang":
        ghi("CANH BAO", "ti le khung", f"{w}x{h} (ngang)", f"{loai} nen dung khung doc",
            "Khung ngang tren dien thoai bi thu nho, mat suc hut")

    # --- 4-7. Do tren cac khung hinh ---
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        moc = {
            "dau": 0.3,
            "mo_dau": min(1.5, dai * 0.05),
            "giua": dai / 2,
            "cuoi": max(0.0, dai - 0.4),
        }
        do = {}
        for ten, giay in moc.items():
            f = t / f"{ten}.jpg"
            if trich_khung(video, giay, f):
                do[ten] = do_khung(f)

        # 4. Khung den dau/cuoi
        for ten, nhan in (("dau", "dau video"), ("cuoi", "cuoi video")):
            if ten in do and do[ten]["do_sang"] < nguong["khung_den_nguong"]:
                ghi("LOI", f"khung den {nhan}",
                    f"do sang {do[ten]['do_sang']}", f"phai tren {NGUONG['khung_den_nguong']}",
                    "Co khung den. Cat bo hoac chinh lai moc bat dau/ket thuc")

        # 5-6. Do sang
        for ten in ("mo_dau", "giua"):
            if ten not in do:
                continue
            s = do[ten]["do_sang"]
            if s < nguong["qua_toi"]:
                ghi("CANH BAO", f"do sang ({ten})", f"{s}", f"nen tren {NGUONG['qua_toi']}",
                    "Hinh toi, xem tren dien thoai ngoai troi se kho nhin")
            elif s > nguong["chay_sang"]:
                ghi("CANH BAO", f"do sang ({ten})", f"{s}", f"nen duoi {NGUONG['chay_sang']}",
                    "Hinh chay sang, mat chi tiet")

        # 7. Mo dau co nguoi khong (THO) - BO QUA voi video do hoa
        if "mo_dau" in do and not la_do_hoa:
            pct = do["mo_dau"]["vung_da_pct"]
            if pct < nguong["da_toi_thieu_pct"]:
                ghi("XEM LAI", "mo dau co nguoi",
                    f"vung mau da {pct}% khung", f"nen tren {NGUONG['da_toi_thieu_pct']}%",
                    "Co the mo dau khong co mat nguoi noi. Luat: mo dau phai la mat nguoi, "
                    "canh phu chi chen TU SAU do. Mo khung hinh ra xem cho chac",
                    tin_cay="thap")

    return loi


def main() -> None:
    ap = argparse.ArgumentParser(description="Cham chat luong video bang nguong so")
    ap.add_argument("video", type=Path)
    ap.add_argument("--loai", default="reel", choices=list(DO_DAI_THEO_LOAI.keys()))
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    if not args.video.exists():
        sys.exit(f"Khong thay file: {args.video}")

    loi = kiem(args.video, args.loai)

    n_loi = sum(1 for m in loi if m["muc"] == "LOI")
    n_canh = sum(1 for m in loi if m["muc"] == "CANH BAO")
    n_xem = sum(1 for m in loi if m["muc"] == "XEM LAI")

    print(f"\nKIEM: {args.video.name}  (loai: {args.loai})")
    print("=" * 72)
    if not loi:
        print("DAT - khong thay van de nao.")
    else:
        for m in loi:
            print(f"[{m['muc']}] {m['phep_kiem']}")
            print(f"    do duoc : {m['so_do']}")
            print(f"    nguong  : {m['nguong']}")
            print(f"    nen lam : {m['khuyen_nghi']}")
            if m["tin_cay"] != "chac":
                print(f"    (tin cay {m['tin_cay']} - kiem lai bang mat)")
            print()
    print("=" * 72)
    print(f"{n_loi} loi | {n_canh} canh bao | {n_xem} can xem lai")
    print("\nLUU Y: may khong bat duoc chu tran khung. Van phai trich khung hinh ra xem.")

    if args.json:
        args.json.write_text(json.dumps(loi, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Da ghi: {args.json}")

    sys.exit(1 if n_loi else 0)


if __name__ == "__main__":
    main()
