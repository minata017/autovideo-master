"""Tim TU DEM va CHO NGAP NGUNG trong ban chu Scribe - de cat bo cho video gon.

Vi sao: nguoi Viet noi hay chen "a", "o", "um", noi lap tu, va nghi giua chung cau.
Truoc day AI phai doc tay ca ban chu roi tu quyet - cham va hay sot. Script nay do
bang may, ra danh sach co MOC GIO de bat/tat tung cho.

Ba loai bat duoc:
  1. TU DEM   - "a", "o", "um", "u", "e"... dung RIENG mot minh giua cau
  2. LAP TU   - noi lap lien nhau ("minh minh", "la la")
  3. IM LANG  - khoang khong co tieng dai hon nguong

THAN TRONG: "a" cung co the la tu co nghia ("A ra the"). Script danh dau muc
TIN CAY, cho nao khong chac thi ghi "can xem lai" chu khong tu cat.

Dung:
    python helpers/tim_tu_dem.py <transcript.scribe.json>
    python helpers/tim_tu_dem.py <video.mp4>            # tu boc bang Scribe truoc
    python helpers/tim_tu_dem.py <file> --nguong-im-lang 0.5 --json ra.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# --- Tu dem tieng Viet ---
# Chi tinh khi dung RIENG mot minh. "a" trong "a lo" khong tinh vi do la mot tu khac.
TU_DEM = {
    "à", "à,", "ạ", "á",
    "ờ", "ừ", "ừm", "um", "ưm",
    "ơ", "ê", "ây",
    "hử", "hở",
}

# ⛔ DA THU VA LOAI BO (kiem tren video that 02/08/2026):
#   "la", "thi"  -> TU NOI, khong phai dem. Ngu canh that:
#                   "toi se bao LA chay quang cao" / "that tot THI nguoi ta se den"
#                   Cat la vo cau. TUYET DOI khong dua lai vao.
#   "a"  (khong dau) -> de nham voi "A lo", "A ra the". Chi bat "a" co dau huyen.
#   "ha" -> tu hoi co nghia ("ha anh?"), khong phai dem.

# Tu dem CHAC CHAN - khong bao gio la tu co nghia khi dung mot minh giua cau
TU_DEM_CHAC = {"à", "ờ", "ừ", "ừm", "um", "ưm", "ơ", "ê", "hử", "hở"}

# Tu KHONG BAO GIO coi la dem du lap (tu noi dung, lap la co y)
KHONG_CAT = {"rất", "very", "không", "nhiều", "lâu", "xa"}


def chuan(s: str) -> str:
    """Bo dau cau, ha thuong, giu dau tieng Viet."""
    s = unicodedata.normalize("NFC", s.strip().lower())
    return re.sub(r"[.,!?;:\-–—…\"'”“]+", "", s).strip()


def doc_ban_chu(duong_dan: Path) -> list[dict]:
    """Doc file Scribe, tra ve danh sach tu {text, start, end}."""
    data = json.loads(duong_dan.read_text(encoding="utf-8"))
    # ban goc Scribe day du
    if isinstance(data, dict) and "words" in data:
        return [w for w in data["words"] if w.get("type") == "word"]
    # ban phang da xu ly (transcript.json cua HyperFrames)
    if isinstance(data, list):
        return data
    sys.exit("Khong hieu dinh dang file ban chu")


def tim(words: list[dict], nguong_im_lang: float) -> list[dict]:
    ket_qua: list[dict] = []

    for i, w in enumerate(words):
        tu = chuan(w["text"])
        if not tu:
            continue

        truoc = chuan(words[i - 1]["text"]) if i > 0 else ""
        sau = chuan(words[i + 1]["text"]) if i + 1 < len(words) else ""

        # --- 1. TU DEM ---
        if tu in TU_DEM:
            if tu in TU_DEM_CHAC:
                tin_cay = "chac"
                ly_do = "tu dem thuan"
            elif tu == truoc or tu == sau:
                tin_cay = "chac"
                ly_do = "lap lien nhau"
            else:
                tin_cay = "xem lai"
                ly_do = "co the la tu co nghia"
            ket_qua.append({
                "loai": "tu_dem",
                "bat_dau": round(float(w["start"]), 2),
                "ket_thuc": round(float(w["end"]), 2),
                "chu": w["text"].strip(),
                "tin_cay": tin_cay,
                "ly_do": ly_do,
            })
            continue

        # --- 2. LAP TU ---
        # Chi tinh khi hai tu NAM TRONG CUNG MOT CAU. Neu tu truoc ket thuc bang
        # dau cham/hoi/than thi day la hai cau khac nhau, khong phai noi lap.
        # (Kiem tren video that 02/08: "ket noi voi toi. Toi den tu Focus" - cat la hong.)
        het_cau = i > 0 and words[i - 1]["text"].rstrip().endswith((".", "!", "?", "…"))

        if tu == truoc and not het_cau and tu not in KHONG_CAT and len(tu) > 1:
            ket_qua.append({
                "loai": "lap_tu",
                "bat_dau": round(float(w["start"]), 2),
                "ket_thuc": round(float(w["end"]), 2),
                "chu": w["text"].strip(),
                "tin_cay": "chac",
                "ly_do": f"lap lai tu truoc ({truoc})",
            })

    # --- 3. IM LANG (khoang trong giua hai tu) ---
    for i in range(len(words) - 1):
        het = float(words[i]["end"])
        bat = float(words[i + 1]["start"])
        khoang = bat - het
        if khoang >= nguong_im_lang:
            ket_qua.append({
                "loai": "im_lang",
                "bat_dau": round(het, 2),
                "ket_thuc": round(bat, 2),
                "chu": "(im lặng)",
                "tin_cay": "chac",
                "ly_do": f"{khoang:.2f}s khong co tieng",
            })

    ket_qua.sort(key=lambda x: x["bat_dau"])
    return ket_qua


def in_bang(kq: list[dict], tong_thoi_luong: float | None) -> None:
    if not kq:
        print("Khong tim thay cho nao can cat.")
        return

    print(f"{'MOC GIO':<17} {'LOAI':<9} {'TIN CAY':<9} CHU")
    print("-" * 62)
    for m in kq:
        moc = f"{m['bat_dau']:>6.2f}-{m['ket_thuc']:<6.2f}"
        chu = m["chu"][:22]
        print(f"{moc:<17} {m['loai']:<9} {m['tin_cay']:<9} {chu}")

    tong_cat = sum(m["ket_thuc"] - m["bat_dau"] for m in kq)
    chac = sum(1 for m in kq if m["tin_cay"] == "chac")
    xem_lai = len(kq) - chac

    print("-" * 62)
    print(f"Tong: {len(kq)} cho  ({chac} chac chan, {xem_lai} can xem lai)")
    for loai in ("tu_dem", "lap_tu", "im_lang"):
        n = sum(1 for m in kq if m["loai"] == loai)
        giay = sum(m["ket_thuc"] - m["bat_dau"] for m in kq if m["loai"] == loai)
        if n:
            print(f"  {loai:<9} {n:>3} cho, {giay:>6.1f}s")
    print(f"Cat het se bo: {tong_cat:.1f}s", end="")
    if tong_thoi_luong:
        print(f" / {tong_thoi_luong:.1f}s ({tong_cat/tong_thoi_luong*100:.0f}%)")
    else:
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Tim tu dem, lap tu, im lang trong ban chu")
    ap.add_argument("nguon", type=Path, help="File ban chu Scribe (.json) hoac video")
    ap.add_argument("--nguong-im-lang", type=float, default=0.35,
                    help="Im lang tu bao nhieu giay thi tinh (mac dinh 0.35)")
    ap.add_argument("--json", type=Path, default=None, help="Ghi ket qua ra file JSON")
    ap.add_argument("--chi-chac", action="store_true",
                    help="Chi lay cho CHAC CHAN, bo cho can xem lai")
    args = ap.parse_args()

    if not args.nguon.exists():
        sys.exit(f"Khong thay file: {args.nguon}")

    duong_dan = args.nguon
    if duong_dan.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".m4a"):
        sys.exit(
            "Day la file media. Boc chu truoc bang:\n"
            f'  python helpers/transcript_hyperframes.py "{duong_dan}" -d <thu-muc>\n'
            "roi chay lai script nay tren file transcript.scribe.json"
        )

    words = doc_ban_chu(duong_dan)
    if not words:
        sys.exit("Ban chu rong")

    kq = tim(words, args.nguong_im_lang)
    if args.chi_chac:
        kq = [m for m in kq if m["tin_cay"] == "chac"]

    tong = float(words[-1]["end"]) if words else None
    in_bang(kq, tong)

    if args.json:
        args.json.write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nDa ghi: {args.json}")


if __name__ == "__main__":
    main()
