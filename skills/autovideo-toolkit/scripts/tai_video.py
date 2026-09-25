"""CUA VAO tu mang: tai video + lay loi thoai ve may, roi giao lai cho xuong.

Day KHONG phai cong cu nhin. Nhin thi da co:
  - timeline_view.py            : soi moc cat (dai phim + song am + nhan tu)
  - soi_phong_cach.py           : hoc phong cach tu video mau (DO ra so), o skill
                                  hieu-ung-video-thuong-hieu
File nay chi lo mot viec ma hai cong cu tren khong lam duoc: **lay video tu mot
duong dan tren mang ve may, kem loi thoai**, roi in ra duong dan de xuong dung tiep.

LUAT CUNG - PHU DE DE DOC, SCRIBE DE CAT:
  Phu de san co tren trang la ban may tu sinh: sai ten rieng (mot lan chay that,
  "Claude" ra thanh clo/claud/claw/cla/lo), moc thoi gian **theo DONG 2-3 giay chu
  khong theo TU**, va khong tach nguoi noi. Dung de doc luot, tim doan, hoc cau
  truc video nguoi khac. HE MA dau ra la mot ban CAT, mot ban phu de chay chu, hay
  mot cau trich nguyen van -> phai boc lai bang Scribe (`--boc-loi`).

Cach dung:
    python helpers/tai_video.py <link>                  # tai video + lay loi
    python helpers/tai_video.py <link> --chi-loi        # khong tai video, chi lay loi
    python helpers/tai_video.py <link> --boc-loi        # ep boc bang Scribe (de CAT)
    python helpers/tai_video.py <link> --thu-muc downloads/
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

THU_MUC_SKILL = Path(__file__).resolve().parent.parent

# Uu tien tieng Viet TRUOC tieng Anh. Ban goc cua cong cu nuoc ngoai viet cung
# "en.*" nen video Viet luon bao "khong co phu de" roi roi xuong boc tinh phi.
CO_PHU_DE = [
    "--write-subs", "--write-auto-subs",
    "--sub-langs", "vi.*,en.*",
    "--sub-format", "vtt", "--convert-subs", "vtt",
]


def bao(msg: str) -> None:
    print(f"[tai] {msg}", file=sys.stderr, flush=True)


def can_co(ten: str) -> None:
    if shutil.which(ten) is None:
        raise SystemExit(
            f"Thieu {ten}. Cai theo Chuong 0 khoa Xuong Video AI "
            f"(ffmpeg: gyan.dev - yt-dlp: uv tool install yt-dlp)."
        )


def la_link(nguon: str) -> bool:
    if nguon.startswith("-"):
        return False
    p = urlparse(nguon)
    return p.scheme in ("http", "https") and bool(p.netloc)


def ghi_gio(giay: float) -> str:
    tong = int(round(giay))
    gio, du = divmod(tong, 3600)
    phut, s = divmod(du, 60)
    return f"{gio}:{phut:02d}:{s:02d}" if gio else f"{phut:02d}:{s:02d}"


# ---------------------------------------------------------------- tai ve

def _chon_phu_de(thu_muc: Path) -> Path | None:
    """Uu tien TIENG VIET (vi-orig = ban goc YouTube nghe ra, hon ban may dich)."""
    ung_vien = sorted(thu_muc.glob("video*.vtt"))
    if not ung_vien:
        return None
    for dau in (".vi-orig", ".vi", ".vi-VN", ".vie"):
        for c in ung_vien:
            if c.name.endswith(dau + ".vtt"):
                return c
    for c in ung_vien:
        if any(d in c.name for d in (".en.", ".en-US.", ".en-GB.", ".en-orig.")):
            return c
    return ung_vien[0]


def _chon_video(thu_muc: Path) -> Path | None:
    for duoi in (".mp4", ".mkv", ".webm", ".mov"):
        for c in thu_muc.glob(f"video*{duoi}"):
            return c
    return None


def doc_tin(duong_dan: Path, link: str) -> dict:
    if not duong_dan.exists():
        return {"url": link}
    try:
        tho = json.loads(duong_dan.read_text(encoding="utf-8"))
    except Exception:
        return {"url": link}
    return {
        "tieu_de": tho.get("title"),
        "kenh": tho.get("uploader") or tho.get("channel"),
        "thoi_luong": tho.get("duration"),
        "url": tho.get("webpage_url") or link,
    }


def hoi_phu_de(link: str, thu_muc: Path) -> dict:
    """Lay thong tin + phu de, CHUA tai video (~10 giay, khong ton dung luong)."""
    can_co("yt-dlp")
    thu_muc.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["yt-dlp", "--skip-download", "--write-info-json", *CO_PHU_DE,
         "--no-playlist", "--ignore-errors",
         "-o", str(thu_muc / "video.%(ext)s"), "--", link],
        stdout=sys.stderr, stderr=sys.stderr,
    )
    return {"phu_de": _chon_phu_de(thu_muc),
            "tin": doc_tin(thu_muc / "video.info.json", link)}


def tai_ve(link: str, thu_muc: Path) -> dict:
    can_co("yt-dlp")
    thu_muc.mkdir(parents=True, exist_ok=True)
    kq = subprocess.run(
        ["yt-dlp", "-N", "8",
         "-f", "bv*[height<=720]+ba/b[height<=720]/bv+ba/b",
         "--merge-output-format", "mp4", "--write-info-json", *CO_PHU_DE,
         "--no-playlist", "--ignore-errors",
         "-o", str(thu_muc / "video.%(ext)s"), "--", link],
        stdout=sys.stderr, stderr=sys.stderr,
    )
    video = _chon_video(thu_muc)
    if video is None:
        raise SystemExit(
            f"yt-dlp khong tai duoc video (ma thoat {kq.returncode}). "
            "Video co the doi dang nhap hoac chan theo vung - tai tay roi chi file cho xuong."
        )
    return {"video": video, "phu_de": _chon_phu_de(thu_muc),
            "tin": doc_tin(thu_muc / "video.info.json", link)}


def co_tieng(video: Path) -> bool:
    can_co("ffprobe")
    kq = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
         str(video.resolve())],
        capture_output=True, text=True,
    )
    if kq.returncode != 0:
        return False
    luong = json.loads(kq.stdout or "{}").get("streams", [])
    return any(s.get("codec_type") == "audio" for s in luong)


# ---------------------------------------------------------------- loi thoai

def doc_vtt(duong_dan: Path) -> list[dict]:
    RE_MOC = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2})[.,](\d{3})")
    RE_THE = re.compile(r"<[^>]+>")
    dong = duong_dan.read_text(encoding="utf-8", errors="ignore").splitlines()
    doan: list[dict] = []
    i = 0
    while i < len(dong):
        m = RE_MOC.match(dong[i])
        if not m:
            i += 1
            continue
        g = m.groups()
        bat_dau = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        ket = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
        i += 1
        chu: list[str] = []
        while i < len(dong) and dong[i].strip():
            sach = RE_THE.sub("", dong[i]).strip()
            if sach:
                chu.append(sach)
            i += 1
        noi_dung = " ".join(chu).strip()
        if noi_dung:
            doan.append({"tu": round(bat_dau, 2), "den": round(ket, 2), "chu": noi_dung})
        i += 1
    return _gom_doan(_bo_chong_lap(doan))


def _bo_chong_lap(doan: list[dict]) -> list[dict]:
    """Phu de tu dong YouTube chay chu: moi cue lap lai phan duoi cue truoc.
    Cat phan lap bang cach so TU - tim doan tu vua la duoi cue truoc vua la dau
    cue sau, chi giu phan moi. (Khong co buoc nay: 303 doan lap thay vi 28 doan sach.)"""
    ra: list[dict] = []
    truoc: list[str] = []
    for d in doan:
        tu_moi = d["chu"].split()
        if not tu_moi:
            continue
        chung = 0
        for k in range(min(len(truoc), len(tu_moi)), 0, -1):
            if truoc[-k:] == tu_moi[:k]:
                chung = k
                break
        con = tu_moi[chung:]
        truoc = tu_moi
        if not con:
            if ra:
                ra[-1]["den"] = d["den"]
            continue
        ra.append({"tu": d["tu"], "den": d["den"], "chu": " ".join(con)})
    return ra


def _gom_doan(doan: list[dict], moi_doan: float = 25.0) -> list[dict]:
    ra: list[dict] = []
    for d in doan:
        if ra and (d["den"] - ra[-1]["tu"]) <= moi_doan:
            ra[-1]["chu"] = (ra[-1]["chu"] + " " + d["chu"]).strip()
            ra[-1]["den"] = d["den"]
        else:
            ra.append(dict(d))
    return ra


def boc_loi_scribe(video: Path, thu_muc: Path) -> list[dict]:
    """Goi helpers/transcribe.py (ElevenLabs Scribe) roi doc file JSON ket qua.
    Khong viet lai gi - dung dung duong boc bang cua xuong, nen ban JSON sinh ra
    dung duoc luon cho pack_transcripts.py / make_lesson_edl.py."""
    kich = THU_MUC_SKILL / "helpers" / "transcribe.py"
    if not kich.exists():
        return []
    lenh = ["uv", "run", "--project", str(THU_MUC_SKILL), "python", str(kich),
            str(video), "--edit-dir", str(thu_muc)]
    if shutil.which("uv") is None:
        lenh = [sys.executable, str(kich), str(video), "--edit-dir", str(thu_muc)]
    kq = subprocess.run(lenh, stdout=sys.stderr, stderr=sys.stderr)
    tep = thu_muc / "transcripts" / f"{video.stem}.json"
    if kq.returncode != 0 or not tep.exists():
        return []
    return _doan_tu_scribe(json.loads(tep.read_text(encoding="utf-8")))


def boc_loi_assemblyai(video: Path, thu_muc: Path) -> list[dict]:
    """Du phong mien phi khi khong co key ElevenLabs: goi
    helpers/transcribe_assemblyai.py (AssemblyAI, luon model tot nhat -
    universal-3-5-pro). Cung schema Scribe. LUU Y: tieng Viet kem hon Scribe,
    ten rieng/tu tieng Anh de sai -> phai qua buoc chinh ngon tu (Hard Rule 13)."""
    kich = THU_MUC_SKILL / "helpers" / "transcribe_assemblyai.py"
    if not kich.exists():
        return []
    lenh = ["uv", "run", "--project", str(THU_MUC_SKILL), "python", str(kich),
            str(video), "--edit-dir", str(thu_muc), "--language", "vi"]
    if shutil.which("uv") is None:
        lenh = [sys.executable, str(kich), str(video), "--edit-dir", str(thu_muc),
                "--language", "vi"]
    kq = subprocess.run(lenh, stdout=sys.stderr, stderr=sys.stderr)
    tep = thu_muc / "transcripts" / f"{video.stem}.json"
    if kq.returncode != 0 or not tep.exists():
        return []
    return _doan_tu_scribe(json.loads(tep.read_text(encoding="utf-8")))


def _doan_tu_scribe(data: dict, cach_quang: float = 25.0) -> list[dict]:
    """Gom tung tu cua Scribe thanh doan - doi nguoi noi hoac qua 25 giay thi xuong dong."""
    doan: list[dict] = []
    dem: list[str] = []
    nguoi = None
    bat_dau = ket = 0.0
    for w in data.get("words", []):
        if w.get("type") == "spacing":
            dem.append(w.get("text", " "))
            continue
        ai = w.get("speaker_id", "?")
        t = w.get("start", ket)
        if nguoi is None:
            nguoi, bat_dau = ai, t
        elif ai != nguoi or (t - ket) > cach_quang or (t - bat_dau) > cach_quang:
            if dem:
                doan.append({"tu": round(bat_dau, 2), "den": round(ket, 2),
                             "chu": "".join(dem).strip(), "ai": nguoi})
            dem, nguoi, bat_dau = [], ai, t
        dem.append(w.get("text", ""))
        ket = w.get("end", t)
    if dem:
        doan.append({"tu": round(bat_dau, 2), "den": round(ket, 2),
                     "chu": "".join(dem).strip(), "ai": nguoi})
    return [d for d in doan if d["chu"]]


def ghi_loi(doan: list[dict]) -> str:
    ra = []
    for d in doan:
        ai = f" ({d['ai']})" if d.get("ai") else ""
        ra.append(f"[{ghi_gio(d['tu'])}]{ai} {d['chu']}")
    return "\n".join(ra)


# ---------------------------------------------------------------- chay chinh

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="tai_video",
        description="Cua vao tu mang: tai video + loi thoai ve may cho xuong dung tiep.")
    ap.add_argument("link", help="Duong dan video tren mang (YouTube, TikTok, Facebook, Vimeo...)")
    ap.add_argument("--chi-loi", action="store_true",
                    help="Chi lay loi thoai, khong tai video (~10 giay, khong ton dung luong)")
    ap.add_argument("--boc-loi", action="store_true",
                    help="EP boc bang Scribe ke ca khi trang da co phu de. "
                         "BAT BUOC khi dau ra la ban CAT hoac phu de chay chu.")
    ap.add_argument("--khong-boc-loi", action="store_true",
                    help="Khong goi Scribe du khong co phu de (giu kin video noi bo)")
    ap.add_argument("--thu-muc", default="downloads",
                    help="Noi luu (mac dinh: downloads/ trong thu muc hien hanh)")
    args = ap.parse_args()

    if not la_link(args.link):
        raise SystemExit(
            "Day khong phai duong dan mang. File san tren may thi dua thang cho "
            "transcribe.py (boc loi) hoac timeline_view.py (nhin)."
        )

    viec = Path(args.thu_muc).expanduser().resolve()
    viec.mkdir(parents=True, exist_ok=True)
    bao(f"thu muc luu: {viec}")

    video: Path | None = None
    bao("hoi thong tin va phu de qua yt-dlp...")
    kq = hoi_phu_de(args.link, viec)
    phu_de, tin = kq["phu_de"], kq["tin"]

    can_tai = not args.chi_loi or args.boc_loi
    if can_tai:
        bao("tai video qua yt-dlp...")
        kq = tai_ve(args.link, viec)
        video, tin = kq["video"], kq["tin"]
        phu_de = kq["phu_de"] or phu_de

    doan: list[dict] = []
    nguon_loi = None
    dung_de_cat = False

    if args.boc_loi and video:
        bao("boc loi bang ElevenLabs Scribe (moc toi tung tu)...")
        doan = boc_loi_scribe(video, viec)
        if doan:
            nguon_loi, dung_de_cat = "ElevenLabs Scribe", True
        else:
            bao("Scribe khong chay duoc -> thu AssemblyAI (mien phi)...")
            doan = boc_loi_assemblyai(video, viec)
            if doan:
                nguon_loi, dung_de_cat = ("AssemblyAI (BAT BUOC chinh ngon tu "
                                          "truoc khi dung - Hard Rule 13)"), True
            else:
                bao(f"Ca Scribe lan AssemblyAI deu khong chay duoc. Kiem "
                    f"ELEVENLABS_API_KEY / ASSEMBLYAI_API_KEY trong {THU_MUC_SKILL / '.env'}.")

    if not doan and phu_de:
        try:
            doan = doc_vtt(Path(phu_de))
            nguon_loi = f"phu de san co tren trang ({Path(phu_de).name})"
        except Exception as e:
            bao(f"doc phu de that bai: {e}")

    if not doan and not args.khong_boc_loi and video and co_tieng(video):
        bao("trang khong co phu de -> boc bang ElevenLabs Scribe...")
        doan = boc_loi_scribe(video, viec)
        if doan:
            nguon_loi, dung_de_cat = "ElevenLabs Scribe", True
        else:
            bao("Scribe khong chay duoc -> thu AssemblyAI (mien phi)...")
            doan = boc_loi_assemblyai(video, viec)
            if doan:
                nguon_loi, dung_de_cat = ("AssemblyAI (BAT BUOC chinh ngon tu "
                                          "truoc khi dung - Hard Rule 13)"), True

    # ---- bao cao
    print()
    print("# Da tai ve")
    print()
    print(f"- **Nguon:** {args.link}")
    if tin.get("tieu_de"):
        print(f"- **Tieu de:** {tin['tieu_de']}")
    if tin.get("kenh"):
        print(f"- **Kenh:** {tin['kenh']}")
    if tin.get("thoi_luong"):
        print(f"- **Do dai:** {ghi_gio(float(tin['thoi_luong']))}")
    if video:
        print(f"- **File video:** `{video}`")
    else:
        print("- **File video:** khong tai (che do chi lay loi)")
    print(f"- **Loi thoai:** {len(doan)} doan (nguon: {nguon_loi})" if doan
          else "- **Loi thoai:** khong lay duoc")

    if doan and not dung_de_cat:
        print()
        print("> **Chu y - ban loi nay DE DOC, KHONG DE CAT.** Phu de tren trang do may "
              "tu sinh: sai ten rieng, moc thoi gian theo DONG 2-3 giay chu khong theo TU, "
              "khong tach nguoi noi. Cat theo no la hut dau hut duoi. Can cat / lam phu de "
              "chay chu / trich nguyen van -> chay lai voi `--boc-loi` (Scribe).")

    print()
    print("## Buoc tiep")
    print()
    if video:
        print(f"- **Nhin video:** `python helpers/timeline_view.py \"{video}\" <giay-dau> <giay-cuoi>`"
              " (them `--rong 1024` khi can doc chu tren man hinh)")
        print("- **Hoc phong cach:** `python scripts/soi_phong_cach.py` trong skill "
              "hieu-ung-video-thuong-hieu (do ra so, mot khung moi canh)")
        if not dung_de_cat:
            print(f"- **Chuan bi CAT:** `python helpers/transcribe.py \"{video}\" --language vie`")

    print()
    print("## Loi thoai")
    print()
    if doan:
        print(f"_Nguon: {nguon_loi}._")
        print()
        print("```")
        print(ghi_loi(doan))
        print("```")
    else:
        print("_Khong co phu de tren trang va cung chua boc tieng._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
