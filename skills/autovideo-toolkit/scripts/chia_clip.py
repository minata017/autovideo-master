"""Chia MOT video dai thanh NHIEU clip ngan - de mot buoi quay thanh ca thang noi dung.

Khong cat bua theo dong ho. Cat tai RANH GIOI TU NHIEN: cho nguoi noi nghi lau
nhat gan moc mong muon. Nho vay clip khong bi hut dau hut duoi cau.

Ra danh sach doan, moi doan co: moc gio, do dai, cau mo dau, so tu.
Nguoi dung xem roi tich chon doan nao muon xuat.

Dung:
    python helpers/chia_clip.py transcript.scribe.json                  # chi de xuat
    python helpers/chia_clip.py transcript.scribe.json --json ra.json
    python helpers/chia_clip.py transcript.scribe.json --dai-muc-tieu 45
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def doc_tu(duong_dan: Path) -> list[dict]:
    d = json.loads(duong_dan.read_text(encoding="utf-8"))
    ws = d["words"] if isinstance(d, dict) else d
    return [w for w in ws if w.get("type", "word") == "word"]


def tim_ranh_gioi(tu: list[dict], dai_muc_tieu: float,
                  dai_toi_thieu: float, dai_toi_da: float) -> list[tuple[float, float]]:
    """Chia thanh doan, moi doan ket thuc tai cho NGHI LAU NHAT gan moc mong muon."""
    if not tu:
        return []

    tong = float(tu[-1]["end"])
    doan: list[tuple[float, float]] = []
    bat_dau = float(tu[0]["start"])
    i = 0

    while i < len(tu):
        moc_mong_muon = bat_dau + dai_muc_tieu
        moc_som_nhat = bat_dau + dai_toi_thieu
        moc_muon_nhat = bat_dau + dai_toi_da

        # tim cho nghi lau nhat trong vung cho phep
        tot_nhat = None
        nghi_lau_nhat = float("-inf")
        j = i
        while j < len(tu) - 1:
            het = float(tu[j]["end"])
            if het < moc_som_nhat:
                j += 1
                continue
            if het > moc_muon_nhat:
                break
            nghi = float(tu[j + 1]["start"]) - het
            # Uu tien: (1) het cau that su - co dau cham/hoi/than
            #          (2) nghi lau
            #          (3) gan moc mong muon
            # Khong co (1) thi clip se bat dau giua cau, nguoi xem nghe hut.
            # (Loi da gap 03/08: clip 2 bat dau bang "minh van phai co y tuong...")
            # Can nang: thuong het cau 3.0, phat 0.15 moi giay lech moc mong muon.
            # Chenh 20 giay la mat het loi the "het cau" -> khong bi hut ve cuoi video.
            # (Loi da gap 03/08: phat qua nhe 0.02 nen cau cuoi video luon thang,
            #  video 63 giay chi ra 1 clip duy nhat.)
            het_cau = tu[j]["text"].rstrip().endswith((".", "!", "?", "…"))
            diem = nghi + (3.0 if het_cau else 0.0) - abs(het - moc_mong_muon) * 0.15
            if diem > nghi_lau_nhat:
                nghi_lau_nhat = diem
                tot_nhat = (j, het)
            j += 1

        if tot_nhat is None:
            # khong con cho nghi nao -> lay het phan con lai
            if tong - bat_dau >= 3.0:
                doan.append((bat_dau, tong))
            break

        j, ket = tot_nhat
        doan.append((bat_dau, ket))
        i = j + 1
        if i >= len(tu):
            break
        bat_dau = float(tu[i]["start"])

        # phan duoi qua ngan thi gop vao doan truoc
        if tong - bat_dau < dai_toi_thieu * 0.6:
            a, _ = doan[-1]
            doan[-1] = (a, tong)
            break

    return doan


def mo_ta_doan(tu: list[dict], bd: float, kt: float) -> dict:
    trong = [w for w in tu if bd <= float(w["start"]) < kt]
    chu = " ".join(w["text"] for w in trong)
    return {
        "bat_dau": round(bd, 2),
        "ket_thuc": round(kt, 2),
        "dai": round(kt - bd, 1),
        "so_tu": len(trong),
        "cau_mo_dau": (chu[:90] + "…") if len(chu) > 90 else chu,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Chia video dai thanh nhieu clip ngan")
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--dai-muc-tieu", type=float, default=55,
                    help="Do dai mong muon moi clip, giay (mac dinh 55)")
    ap.add_argument("--dai-toi-thieu", type=float, default=22)
    ap.add_argument("--dai-toi-da", type=float, default=95)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    if not args.transcript.exists():
        sys.exit(f"Khong thay file: {args.transcript}")

    tu = doc_tu(args.transcript)
    if not tu:
        sys.exit("Ban chu rong")

    tong = float(tu[-1]["end"])
    if tong < args.dai_toi_thieu * 1.6:
        print(f"Video chi dai {tong:.0f}s - qua ngan de chia. Giu nguyen mot clip.")
        doan = [(float(tu[0]["start"]), tong)]
    else:
        doan = tim_ranh_gioi(tu, args.dai_muc_tieu, args.dai_toi_thieu, args.dai_toi_da)

    ds = [mo_ta_doan(tu, a, b) for a, b in doan]

    print(f"Video dai {tong:.0f}s -> chia thanh {len(ds)} clip\n")
    print(f"{'#':<3} {'MOC GIO':<16} {'DAI':>6}  CAU MO DAU")
    print("-" * 76)
    for i, d in enumerate(ds, 1):
        moc = f"{d['bat_dau']:.1f}-{d['ket_thuc']:.1f}"
        print(f"{i:<3} {moc:<16} {d['dai']:>5.0f}s  {d['cau_mo_dau'][:52]}")

    if args.json:
        args.json.write_text(json.dumps(ds, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nDa ghi: {args.json}")


if __name__ == "__main__":
    main()
