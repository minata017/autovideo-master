#!/usr/bin/env python3
"""Tim, tai va chen video B-roll tu Pixabay.

Su dung:
  # Buoc 1: Tim canh B-roll
  python tim-broll.py --canh temp/canh-can-broll.json --khung 9:16

  # Buoc 2: Tai video da duyet
  python tim-broll.py --canh temp/canh-can-broll.json --khung 9:16 --tai
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    print("[pixabay] LOI: Thu vien 'requests' chua cai. Chay: pip install requests")
    sys.exit(1)

# Thu muc goc du an
BASE_DIR = Path(__file__).resolve().parents[3]  # skills/pixabay-broll/scripts -> root
TEMP_DIR = BASE_DIR / "temp"
BROLL_DIR = TEMP_DIR / "broll"

PIXABAY_API_URL = "https://pixabay.com/api/videos/"


def doc_api_key():
    """Doc PIXABAY_API_KEY tu file .env"""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("PIXABAY_API_KEY=") and not line.startswith("#"):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val and val != "your_pixabay_api_key_here" and val != "":
                return val
    return None


def tim_video_pixabay(api_key, keyword, khung="9:16", so_luong=5):
    """Tim video tren Pixabay theo keyword va khung hinh.

    Tra ve danh sach hits da loc theo huong man hinh.
    """
    params = {
        "key": api_key,
        "q": keyword,
        "video_type": "film",
        "safesearch": "true",
        "per_page": min(so_luong * 3, 50),  # Lay nhieu hon de loc
        "order": "popular",
    }

    # Loc theo kich thuoc toi thieu
    if khung == "9:16":
        params["min_height"] = 720
    else:
        params["min_width"] = 720

    try:
        resp = requests.get(PIXABAY_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[pixabay] LOI goi API: {e}")
        return []

    if data.get("totalHits", 0) == 0:
        return []

    # Loc theo huong man hinh
    ket_qua = []
    for hit in data.get("hits", []):
        # Chon resolution phu hop nhat (large -> medium -> small -> tiny)
        video_info = chon_resolution(hit.get("videos", {}), khung)
        if not video_info:
            continue

        w = video_info["width"]
        h = video_info["height"]

        # Kiem tra huong man hinh
        if khung == "9:16":
            # Uu tien video doc (h > w), nhung van chap nhan ngang de crop
            diem = 2 if h > w else 1
        else:
            diem = 2 if w > h else 1

        ket_qua.append({
            "id": hit["id"],
            "tags": hit.get("tags", ""),
            "duration": hit.get("duration", 0),
            "url": video_info["url"],
            "width": w,
            "height": h,
            "size_mb": round(video_info.get("size", 0) / 1024 / 1024, 1),
            "page_url": hit.get("pageURL", ""),
            "user": hit.get("user", ""),
            "huong_diem": diem,
        })

    # Sap xep: uu tien video dung huong, sau do theo luot xem
    ket_qua.sort(key=lambda x: (-x["huong_diem"], -x.get("duration", 0)))
    return ket_qua[:so_luong]


def chon_resolution(videos_dict, khung):
    """Chon ban video co resolution phu hop nhat.

    Duyet large -> medium -> small -> tiny.
    Chon ban >= 720p gan nhat. KHONG gia dinh ban nao la 1080p.
    """
    muc_tieu_min = 720  # Toi thieu 720p
    thu_tu = ["large", "medium", "small", "tiny"]

    tot_nhat = None
    for key in thu_tu:
        v = videos_dict.get(key)
        if not v or not v.get("url"):
            continue

        w = v.get("width", 0)
        h = v.get("height", 0)

        if khung == "9:16":
            # Can height >= 720
            if h >= muc_tieu_min:
                if tot_nhat is None or h < tot_nhat["height"]:
                    # Chon ban nho nhat dat yeu cau (tiet kiem bang thong)
                    tot_nhat = v
        else:
            # Can width >= 720
            if w >= muc_tieu_min:
                if tot_nhat is None or w < tot_nhat["width"]:
                    tot_nhat = v

    # Fallback: neu khong ban nao dat yeu cau, lay ban lon nhat co san
    if tot_nhat is None:
        for key in thu_tu:
            v = videos_dict.get(key)
            if v and v.get("url"):
                return v
    return tot_nhat


def rut_keyword(cau):
    """Rut keyword tim kiem tu cau tieng Viet.

    Giu danh tu chinh, bo tu dem va lien tu.
    """
    # Danh sach tu bo (tieng Viet pho bien)
    bo_tu = {
        "la", "cua", "va", "nhung", "cac", "mot", "nhu", "tai", "trong",
        "cho", "voi", "dang", "da", "se", "duoc", "co", "khong", "rat",
        "nay", "do", "khi", "thi", "ma", "de", "tu", "den", "bang",
        "là", "của", "và", "những", "các", "một", "như", "tại", "trong",
        "cho", "với", "đang", "đã", "sẽ", "được", "có", "không", "rất",
        "này", "đó", "khi", "thì", "mà", "để", "từ", "đến", "bằng",
    }

    # Tach tu va loc
    tu_list = cau.lower().split()
    tu_giu = [t for t in tu_list if t not in bo_tu and len(t) > 1]

    # Gioi han 3-4 tu cho query
    return " ".join(tu_giu[:4])


def tai_video(url, output_path, timeout=60):
    """Tai video tu URL ve local."""
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"[pixabay] LOI tai video: {e}")
        return False


def xu_ly_broll(input_path, output_path, start, end, khung, ffmpeg_path="ffmpeg"):
    """Cat video B-roll dung do dai va xu ly khung hinh.

    - Mute audio goc
    - Crop/scale theo khung hinh muc tieu
    """
    duration = end - start

    if khung == "9:16":
        target_w, target_h = 1080, 1920
    else:
        target_w, target_h = 1920, 1080

    # Filter: scale + crop ve dung khung hinh + mute audio
    vf = (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
        f"crop={target_w}:{target_h}"
    )

    cmd = [
        ffmpeg_path, "-y",
        "-i", str(input_path),
        "-t", str(round(duration, 2)),
        "-vf", vf,
        "-an",  # Mute audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def tim_ffmpeg():
    """Tim duong dan FFmpeg."""
    # Kiem tra PATH
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
        if result.returncode == 0:
            return "ffmpeg"
    except FileNotFoundError:
        pass

    # Tim trong AppData
    appdata = Path(os.environ.get("LOCALAPPDATA", ""))
    if appdata.exists():
        for f in appdata.glob("ffmpeg/ffmpeg-*/bin/ffmpeg.exe"):
            return str(f)

    return None


def main():
    parser = argparse.ArgumentParser(description="Tim va tai video B-roll tu Pixabay")
    parser.add_argument("--canh", required=True, help="File JSON danh sach canh can B-roll")
    parser.add_argument("--khung", default="9:16", choices=["9:16", "16:9"],
                        help="Khung hinh muc tieu (mac dinh: 9:16)")
    parser.add_argument("--tai", action="store_true",
                        help="Tai va xu ly video (neu khong chi: tim va de xuat)")
    parser.add_argument("--output", default=None,
                        help="Thu muc/file xuat ket qua")
    args = parser.parse_args()

    # Doc API key
    api_key = doc_api_key()
    if not api_key:
        print("=" * 60)
        print("  PIXABAY B-ROLL: CHUA CO API KEY")
        print("=" * 60)
        print("Dien PIXABAY_API_KEY vao file .env tai thu muc goc du an.")
        print("Lay khoa mien phi tai: https://pixabay.com/api/docs/")
        print("=" * 60)
        sys.exit(1)

    # Doc danh sach canh
    canh_file = Path(args.canh)
    if not canh_file.exists():
        print(f"[pixabay] LOI: Khong tim thay file {canh_file}")
        sys.exit(1)

    with open(canh_file, "r", encoding="utf-8") as f:
        danh_sach_canh = json.load(f)

    print("=" * 60)
    print("  PIXABAY B-ROLL: TIM CANH PHU HOP")
    print("=" * 60)
    print(f"[pixabay] So canh can tim: {len(danh_sach_canh)}")
    print(f"[pixabay] Khung hinh: {args.khung}")

    # Tim video cho tung canh
    de_xuat = []
    for i, canh in enumerate(danh_sach_canh):
        cau = canh.get("cau", "")
        start = canh.get("start", 0)
        end = canh.get("end", 0)
        keyword = canh.get("keyword_goi_y", "") or rut_keyword(cau)
        cau_ngan = cau[:50] + "..." if len(cau) > 50 else cau
        print(f"\n[{i+1}/{len(danh_sach_canh)}] {cau_ngan}")
        print(f"  Keyword: {keyword} | {start:.1f}s - {end:.1f}s")

        hits = tim_video_pixabay(api_key, keyword, args.khung, so_luong=3)

        if not hits:
            # Thu keyword rong hon
            keyword_rong = keyword.split()[0] if " " in keyword else keyword
            print(f"  Khong tim thay, thu keyword rong hon: {keyword_rong}")
            hits = tim_video_pixabay(api_key, keyword_rong, args.khung, so_luong=3)

        if hits:
            best = hits[0]
            print(f"  Tim thay: ID {best['id']} | {best['width']}x{best['height']} | "
                  f"{best['duration']}s | {best['size_mb']}MB")
            de_xuat.append({
                "stt": i + 1,
                "cau": cau,
                "keyword": keyword,
                "start": start,
                "end": end,
                "pixabay_id": best["id"],
                "pixabay_url": best["url"],
                "page_url": best["page_url"],
                "user": best["user"],
                "width": best["width"],
                "height": best["height"],
                "duration": best["duration"],
                "size_mb": best["size_mb"],
            })
        else:
            print(f"  KHONG TIM THAY canh phu hop. Dung file trong input/broll/")
            de_xuat.append({
                "stt": i + 1,
                "cau": cau,
                "keyword": keyword,
                "start": start,
                "end": end,
                "pixabay_id": None,
                "loi": "Khong tim thay video phu hop tren Pixabay",
            })

    # Luu de xuat
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_file = Path(args.output) if args.output else TEMP_DIR / "broll-de-xuat.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(de_xuat, f, ensure_ascii=False, indent=2)

    # In bang de xuat
    print("\n" + "=" * 60)
    print("  DANH SACH CANH DE XUAT")
    print("=" * 60)
    for dx in de_xuat:
        status = f"Pixabay #{dx['pixabay_id']} ({dx.get('width','?')}x{dx.get('height','?')})" if dx.get("pixabay_id") else "KHONG CO"
        print(f"  [{dx['stt']}] {dx['cau'][:40]}...")
        print(f"      {dx['start']:.1f}s-{dx['end']:.1f}s | {status}")
    print("=" * 60)
    print(f"[pixabay] De xuat da luu: {output_file}")

    # Tai video neu co flag --tai
    if args.tai:
        print("\n[pixabay] Bat dau tai va xu ly video B-roll...")
        ffmpeg_path = tim_ffmpeg()
        if not ffmpeg_path:
            print("[pixabay] LOI: Khong tim thay FFmpeg!")
            sys.exit(1)

        BROLL_DIR.mkdir(parents=True, exist_ok=True)
        sources = []

        for dx in de_xuat:
            if not dx.get("pixabay_id"):
                continue

            raw_path = BROLL_DIR / f"raw-{dx['stt']}.mp4"
            final_path = BROLL_DIR / f"broll-{dx['stt']}.mp4"

            print(f"  [{dx['stt']}] Tai Pixabay #{dx['pixabay_id']}...", end=" ")
            if tai_video(dx["pixabay_url"], raw_path):
                print("OK.", end=" ")
                # Xu ly khung hinh + cat do dai
                if xu_ly_broll(raw_path, final_path, dx["start"], dx["end"],
                               args.khung, ffmpeg_path):
                    print(f"Xu ly xong: {final_path.name}")
                    sources.append({
                        "stt": dx["stt"],
                        "pixabay_id": dx["pixabay_id"],
                        "page_url": dx.get("page_url", ""),
                        "user": dx.get("user", ""),
                        "file": str(final_path),
                    })
                else:
                    print("LOI xu ly FFmpeg!")
                # Xoa file raw
                raw_path.unlink(missing_ok=True)
            else:
                print("LOI tai!")

        # Ghi link nguon
        sources_file = TEMP_DIR / "broll-sources.json"
        with open(sources_file, "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
        print(f"\n[pixabay] Link nguon da ghi: {sources_file}")
        print(f"[pixabay] Video B-roll tai: {BROLL_DIR}")

    print("\n[pixabay] Hoan tat!")


if __name__ == "__main__":
    main()
