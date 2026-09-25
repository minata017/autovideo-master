"""Chon khung dep nhat trong video roi lam THUMBNAIL - ra nhieu ban de chon.

Hai buoc:
  1. CHON KHUNG - quet ca video, cham diem tung khung, lay top N ung vien
     Cham theo 4 tieu chi: co mat nguoi (vung mau da) · net (khong mo) ·
     sang vua (khong toi khong chay) · giau chi tiet
  2. LAM THUMBNAIL - lay 3 khung diem cao nhat, dap chu theo GU (mau + font
     lay tu kho gu chung, cung nguon voi HyperFrames)

Ra:
  <thu-muc>/khung/cand00..NN.jpg   - cac ung vien, ten co kem diem
  <thu-muc>/thumb-v1.png v2 v3     - 3 ban thumbnail de chon

Dung:
    python helpers/lam_thumbnail.py video.mp4 -d ra/
    python helpers/lam_thumbnail.py video.mp4 -d ra/ --chu "LỜI CẢM ƠN" --gu mac-dinh
    python helpers/lam_thumbnail.py video.mp4 -d ra/ --so-ung-vien 12 --khong-mat-nguoi
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TRONG_SO = {
    "mat_nguoi": 0.40,   # co nguoi trong khung = quan trong nhat voi video nguoi noi
    "net": 0.30,         # khung mo la hong
    "sang": 0.20,
    "chi_tiet": 0.10,
}


def chay(cmd: list[str]) -> None:
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def do_dai(video: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def cham_diem(duong_dan: Path, tinh_mat_nguoi: bool) -> dict:
    """Cham mot khung tren thang 0-100."""
    img = Image.open(duong_dan).convert("RGB")
    a = np.asarray(img).astype(np.float32)
    xam = a.mean(axis=2)

    # NET: do lech cua chenh lech pixel ke nhau. Khung mo -> chenh lech thap.
    gx = np.abs(np.diff(xam, axis=1)).mean()
    gy = np.abs(np.diff(xam, axis=0)).mean()
    net_tho = (gx + gy) / 2
    net = min(100.0, net_tho / 12.0 * 100)

    # SANG: gan 128 la tot nhat, cang xa cang tru diem
    tb = float(xam.mean())
    sang = max(0.0, 100 - abs(tb - 128) / 128 * 100)

    # CHI TIET: do lech chuan pixel - khung phang lì thi thap
    chi_tiet = min(100.0, float(xam.std()) / 70.0 * 100)

    # MAT NGUOI (tho, qua vung mau da)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    da = (
        (r > 80) & (r < 255) & (g > 45) & (g < 220) & (b > 30) & (b < 200)
        & (r > g + 12) & (g > b - 5) & (r > b + 10)
    )
    da_pct = float(da.mean() * 100)
    # 6-35% vung da la khoang dep (chan dung). It qua = khong co nguoi,
    # nhieu qua = mat qua sat man hinh.
    if da_pct < 1:
        mat_nguoi = 0.0
    elif da_pct < 6:
        mat_nguoi = da_pct / 6 * 70
    elif da_pct <= 35:
        mat_nguoi = 100.0
    else:
        mat_nguoi = max(40.0, 100 - (da_pct - 35) * 1.5)

    ts = dict(TRONG_SO)
    if not tinh_mat_nguoi:
        # video do hoa: bo tieu chi mat nguoi, chia lai trong so
        ts.pop("mat_nguoi")
        tong = sum(ts.values())
        ts = {k: v / tong for k, v in ts.items()}
        diem = net * ts["net"] + sang * ts["sang"] + chi_tiet * ts["chi_tiet"]
    else:
        diem = (mat_nguoi * ts["mat_nguoi"] + net * ts["net"]
                + sang * ts["sang"] + chi_tiet * ts["chi_tiet"])

    # ep ve float thuong - numpy float32 khong ghi JSON duoc (loi da gap 02/08)
    return {
        "diem": round(float(diem), 1),
        "mat_nguoi": round(float(mat_nguoi), 1),
        "net": round(float(net), 1),
        "sang": round(float(sang), 1),
        "chi_tiet": round(float(chi_tiet), 1),
        "vung_da_pct": round(float(da_pct), 1),
    }


def nap_gu(ten_gu: str | None) -> dict:
    """Lay mau + font tu kho gu chung. Khong co thi dung mac dinh."""
    mac_dinh = {
        "nen": "#0B0F1A", "chu": "#F3F4F6", "nhan": "#E2562B",
        "fonts": [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"],
    }
    if not ten_gu:
        return mac_dinh
    # Kho gu nam trong chinh bo cong cu (thu muc `kho-gu/`).
    # Muon de cho khac thi dat bien moi truong KHO_GU tro toi thu muc do.
    kho = Path(os.environ.get("KHO_GU") or (Path(__file__).resolve().parent.parent / "kho-gu"))
    for thu in (kho / "san-pham" / f"{ten_gu}.json", kho / f"{ten_gu}.json"):
        if thu.exists():
            g = json.loads(thu.read_text(encoding="utf-8"))
            return {
                "nen": g["mau"]["nen"], "chu": g["mau"]["chu"], "nhan": g["mau"]["nhan"],
                "fonts": g.get("chu", {}).get("font_may", mac_dinh["fonts"]),
            }
    print(f"  (khong thay gu '{ten_gu}' trong kho, dung mau mac dinh)")
    return mac_dinh


def nap_font(gu: dict, co: int) -> ImageFont.FreeTypeFont:
    for fp in gu["fonts"]:
        try:
            return ImageFont.truetype(fp, co)
        except Exception:
            continue
    return ImageFont.load_default()


def dap_chu(khung: Path, chu: str, gu: dict, kieu: int, ra: Path) -> None:
    """Dap chu len khung theo 3 kieu bo cuc khac nhau."""
    img = Image.open(khung).convert("RGB")
    W, H = img.size
    ve = ImageDraw.Draw(img, "RGBA")

    co = int(H * 0.075)
    font = nap_font(gu, co)
    hop = ve.textbbox((0, 0), chu, font=font)
    tw, th = hop[2] - hop[0], hop[3] - hop[1]

    if kieu == 1:
        # Kieu 1: dai mau nhan duoi chan, chu trang tren dai
        cao = int(th * 2.2)
        ve.rectangle([0, H - cao, W, H], fill=gu["nhan"] + "F0")
        ve.text(((W - tw) / 2, H - cao + (cao - th) / 2 - hop[1]), chu,
                font=font, fill=gu["chu"])
    elif kieu == 2:
        # Kieu 2: vet toi tu duoi len, chu to o 1/3 duoi
        lop = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        v2 = ImageDraw.Draw(lop)
        for i in range(int(H * 0.45)):
            y = H - i
            mo = int(215 * (i / (H * 0.45)) ** 0.7)
            v2.line([(0, y), (W, y)], fill=(11, 15, 26, mo))
        img = Image.alpha_composite(img.convert("RGBA"), lop).convert("RGB")
        ve = ImageDraw.Draw(img)
        y = int(H * 0.74)
        ve.text(((W - tw) / 2, y), chu, font=font, fill=gu["chu"])
        ve.rectangle([(W - tw) / 2, y + th + int(H * 0.022),
                      (W + tw) / 2, y + th + int(H * 0.030)], fill=gu["nhan"])
    else:
        # Kieu 3: hop chu nam giua, nen toi mo, vien mau nhan ben trai
        dem = int(co * 0.55)
        x0, y0 = (W - tw) / 2 - dem, H * 0.42 - dem
        x1, y1 = (W + tw) / 2 + dem, H * 0.42 + th + dem
        ve.rectangle([x0, y0, x1, y1], fill=gu["nen"] + "DC")
        ve.rectangle([x0, y0, x0 + max(6, int(W * 0.012)), y1], fill=gu["nhan"])
        ve.text(((W - tw) / 2, H * 0.42 - hop[1]), chu, font=font, fill=gu["chu"])

    img.save(ra, quality=95)


def main() -> None:
    ap = argparse.ArgumentParser(description="Chon khung dep + lam thumbnail nhieu ban")
    ap.add_argument("video", type=Path)
    ap.add_argument("-d", "--thu-muc", type=Path, required=True)
    ap.add_argument("--chu", default=None, help="Chu dap len thumbnail")
    ap.add_argument("--gu", default=None, help="Ten gu trong kho gu (mau + font)")
    ap.add_argument("--so-ung-vien", type=int, default=10)
    ap.add_argument("--quet", type=int, default=60, help="So khung quet ra de cham")
    ap.add_argument("--khong-mat-nguoi", action="store_true",
                    help="Video do hoa - bo tieu chi co mat nguoi")
    args = ap.parse_args()

    if not args.video.exists():
        sys.exit(f"Khong thay file: {args.video}")

    dai = do_dai(args.video)
    thu_muc_khung = args.thu_muc / "khung"
    thu_muc_khung.mkdir(parents=True, exist_ok=True)

    print(f"Quet {args.quet} khung tren {dai:.1f}s...")
    ket = []
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for i in range(args.quet):
            giay = dai * (i + 0.5) / args.quet
            f = t / f"q{i:03d}.jpg"
            chay(["ffmpeg", "-v", "error", "-ss", str(giay), "-i", str(args.video),
                  "-frames:v", "1", "-vf", "scale=480:-1", "-y", str(f)])
            if not f.exists() or f.stat().st_size == 0:
                continue
            d = cham_diem(f, not args.khong_mat_nguoi)
            d["giay"] = round(giay, 2)
            ket.append(d)

        if not ket:
            sys.exit("Khong trich duoc khung nao")

        ket.sort(key=lambda x: -x["diem"])
        top = ket[:args.so_ung_vien]

        # trich lai o do phan giai day du
        for i, d in enumerate(top):
            ra = thu_muc_khung / f"cand{i:02d}_diem{int(d['diem'])}_{d['giay']:.1f}s.jpg"
            chay(["ffmpeg", "-v", "error", "-ss", str(d["giay"]), "-i", str(args.video),
                  "-frames:v", "1", "-q:v", "2", "-y", str(ra)])
            d["file"] = str(ra)

    print(f"\n{'HANG':<5} {'GIAY':>7} {'DIEM':>6} {'NGUOI':>6} {'NET':>6} {'SANG':>6}")
    print("-" * 44)
    for i, d in enumerate(top):
        print(f"{i:<5} {d['giay']:>7.1f} {d['diem']:>6.1f} "
              f"{d['mat_nguoi']:>6.1f} {d['net']:>6.1f} {d['sang']:>6.1f}")

    (args.thu_muc / "diem-khung.json").write_text(
        json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.chu:
        gu = nap_gu(args.gu)
        print(f"\nLam 3 ban thumbnail voi chu: {args.chu}")
        for kieu in (1, 2, 3):
            nguon = Path(top[min(kieu - 1, len(top) - 1)]["file"])
            ra = args.thu_muc / f"thumb-v{kieu}.jpg"
            dap_chu(nguon, args.chu, gu, kieu, ra)
            print(f"  thumb-v{kieu}.jpg  (tu khung {top[min(kieu-1, len(top)-1)]['giay']:.1f}s)")

    print(f"\nXong. Xem trong: {args.thu_muc}")


if __name__ == "__main__":
    main()
