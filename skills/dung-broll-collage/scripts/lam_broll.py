#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lam_broll.py - CONG VAO cua skill dung-broll-collage.

Skill CHINH (bien tap video) ra lenh -> script nay sinh canh tram collage
-> tra ve file mp4 CAM dung do dai yeu cau. Skill chinh tu ghep vao video.

Script KHONG tu tim cho tram, KHONG tu ghep. Do la viec cua skill chinh.

Chay bang HYPERFRAMES (da co san tu buoi 3 cua lop) - khong cai them gi.

DUNG:
  # Mot canh
  python lam_broll.py --loi "AI cat ghep thay ban" --giay 4 --fps 30 --khung 9:16 \
      --ra "duong/dan/b1.mp4"

  # Ca loat (khuyen dung - tu tranh trung canh va mau giua cac doan)
  python lam_broll.py --bang yeucau.json --thu-muc "duong/dan/broll"

  # Duyet re: chi ra anh tinh, khong render video
  python lam_broll.py --loi "..." --giay 3 --ra out/a.mp4 --xem-truoc

TRA VE: in JSON bang ke ra man hinh (skill chinh doc de biet duong dan + do dai that).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Windows in ra man hinh bang cp1252 -> duong dan/loi thoai co dau tieng Viet
# lam CHET script NGAY SAU KHI da render xong (skill chinh tuong that bai).
for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canh import DS_CANH, defs  # noqa: E402

# Thu vien lam dong nam NGAY TRONG skill -> chay duoc khi khong co mang.
GSAP = os.path.normpath(os.path.join(HERE, "..", "vendor", "gsap.min.js"))

KHUNG = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

# ============================================================
# BANG CANH: chon AN DU HINH theo nghia cau noi.
# Khong co no thi moi cau deu ra cung mot hinh -> chen 5 cho la 5 lan giong het.
# Them canh moi: viet ham trong canh.py -> dang ky DS_CANH -> them 1 dong o day.
# ============================================================
BANG_CANH = [
    ("thoi-gian-troi", {
        "y": "thoi gian troi, mat thoi gian, cham chap, lam thu cong",
        "tu": ["thoi gian", "thời gian", "mất", "cham", "chậm", "lau", "lâu",
               "ca ngay", "cả ngày", "hang gio", "hàng giờ", "thu cong", "thủ công",
               "moi ngay", "mỗi ngày", "tre", "trễ", "deadline", "tieng", "tiếng",
               "phut", "phút", "tuan", "tuần", "ngay dem", "ngày đêm"],
    }),
    ("hon-loan-ngan-nap", {
        "y": "hon loan -> ngan nap, kien thuc rai rac, bo nao thu 2, he thong hoa",
        "tu": ["lon xon", "lộn xộn", "hon loan", "hỗn loạn", "bua bon", "bừa bộn",
               "rai rac", "rải rác", "that lac", "thất lạc", "quen", "quên",
               "tim lai", "tìm lại", "sap xep", "sắp xếp", "ngan nap", "ngăn nắp",
               "he thong", "hệ thống", "bo nao", "bộ não", "kien thuc", "kiến thức",
               "tai lieu", "tài liệu", "ghi chu", "ghi chú", "luu tru", "lưu trữ",
               "quan ly", "quản lý", "gon gang", "gọn gàng"],
    }),
    ("tang-truong", {
        "y": "tang truong, doanh thu, ket qua di len, nhan doi",
        "tu": ["tang truong", "tăng trưởng", "doanh thu", "loi nhuan", "lợi nhuận",
               "tang", "tăng", "gap doi", "gấp đôi", "nhan doi", "nhân đôi",
               "x2", "x3", "ket qua", "kết quả", "hieu qua", "hiệu quả",
               "don hang", "đơn hàng", "khach hang", "khách hàng", "ban duoc",
               "bán được", "tien", "tiền", "thu nhap", "thu nhập", "bua pha", "bứt phá"],
    }),
    ("may-lam-thay", {
        "y": "AI / may lam thay nguoi / tu dong hoa",
        "tu": ["ai lam", "ai se", "ai ", " ai", "tu dong", "tự động", "may lam",
               "máy làm", "thay ban", "thay bạn", "thay nguoi", "thay người",
               "robot", "cong nghe", "công nghệ", "phan mem", "phần mềm",
               "cong cu", "công cụ", "tro ly", "trợ lý", "agent", "chay ngam",
               "chạy ngầm", "24/7", "giai phong", "giải phóng"],
    }),
    ("quay-cat-xuat-ban", {
        "y": "lam video, dung phim, quy trinh, cac buoc (canh mac dinh)",
        "tu": ["video", "quay", "dung phim", "dựng phim", "cat ghep", "cắt ghép",
               "bien tap", "biên tập", "hau ky", "hậu kỳ", "quy trinh", "quy trình",
               "cac buoc", "các bước", "reels", "tiktok", "youtube", "kenh", "kênh",
               "noi dung", "nội dung", "dang bai", "đăng bài"],
    }),
]
CANH_MAC_DINH = "quay-cat-xuat-ban"

BANG_MAU = [
    (["quy trinh", "quy trình", "he thong", "hệ thống", "cach lam", "cách làm",
      "dung video", "dựng video", "buoc", "bước"],
     {"bg": "#1b7d70", "accent": "#e8b23a", "pop": "#e0503a"}),
    (["sai lam", "sai lầm", "canh bao", "cảnh báo", "mat", "mất", "that bai",
      "thất bại", "dung lai", "dừng lại", "nguy"],
     {"bg": "#b3402e", "accent": "#e8b23a", "pop": "#f3ead6"}),
    (["tien", "tiền", "doanh thu", "loi nhuan", "lợi nhuận", "gia", "giá",
      "khach hang", "khách hàng", "ban", "bán"],
     {"bg": "#c9962e", "accent": "#1b7d70", "pop": "#b3402e"}),
    (["ai", "cong nghe", "công nghệ", "tuong lai", "tương lai", "tu dong",
      "tự động", "robot", "may", "máy"],
     {"bg": "#3b3560", "accent": "#e8b23a", "pop": "#e0503a"}),
]
MAU_MAC_DINH = {"bg": "#1b7d70", "accent": "#e8b23a", "pop": "#e0503a"}
CREAM, CREAM_E, INK = "#f3ead6", "#ddd0af", "#1d1b1a"


def chon_canh(loi, da_dung):
    """Chon an du theo nghia cau noi; tranh lap canh vua dung lien truoc."""
    t = (loi or "").lower()
    diem = []
    for ten, info in BANG_CANH:
        d = sum(1 for k in info["tu"] if k.lower() in t)
        if d:
            diem.append((d, ten))
    if not diem:
        return CANH_MAC_DINH
    diem.sort(reverse=True)
    if da_dung and diem[0][1] == da_dung[-1] and len(diem) > 1:
        return diem[1][1]
    return diem[0][1]


def chon_mau(loi, da_dung):
    """Chon bo mau theo nghia cau noi; tranh trung mau canh lien truoc."""
    t = (loi or "").lower()
    ung_vien = [m for tu, m in BANG_MAU if any(k in t for k in tu)] or [MAU_MAC_DINH]
    for m in ung_vien:
        if not da_dung or m["bg"] != da_dung[-1]:
            return m
    for _, m in BANG_MAU:
        if not da_dung or m["bg"] != da_dung[-1]:
            return m
    return ung_vien[0]


def tong_mau_tu_video(video, giay):
    """Lay mau trung binh 1 khung tai moc -> canh tram hop tone video chinh."""
    try:
        out = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(max(0, giay)), "-i", video,
             "-frames:v", "1", "-vf", "scale=1:1", "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-"],
            capture_output=True, timeout=60)
        b = out.stdout
        if len(b) >= 3:
            return "#%02x%02x%02x" % (b[0], b[1], b[2])
    except Exception:
        pass
    return None


def kiem_cong_cu():
    """Bao loi RO khi thieu cong cu thay vi de lenh chet kho hieu."""
    thieu = []
    for ten, lenh in (("Node.js", "node -v"), ("ffmpeg", "ffmpeg -version"),
                      ("ffprobe", "ffprobe -version")):
        try:
            if subprocess.run(lenh, shell=True, capture_output=True, timeout=90).returncode != 0:
                thieu.append(ten)
        except Exception:
            thieu.append(ten)
    if thieu:
        sys.exit("Máy chưa có: " + ", ".join(thieu) + ".\n"
                 "Cài Node.js tại https://nodejs.org, ffmpeg tại https://ffmpeg.org\n"
                 "rồi mở lại Claude Code và thử lại.")


def dung_html(canh, giay, w, h, mau):
    """Rap composition HyperFrames: SVG (hinh) + GSAP (lam dong)."""
    M = dict(mau)
    M.update({"cream": CREAM, "creamE": CREAM_E, "ink": INK})
    L = {"wide": w > h * 1.15, "square": (not w > h * 1.15) and w > h * 0.9}
    svg, js = DS_CANH[canh](L, M)
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="UTF-8"/>
<script src="gsap.min.js"></script>
<style>
  body {{ margin:0; background:{M['bg']}; }}
  #root {{ position:relative; width:{w}px; height:{h}px; overflow:hidden; background:{M['bg']}; }}
  .clip {{ position:absolute; inset:0; }}
</style></head>
<body>
<div id="root" data-composition-id="broll" data-start="0"
     data-width="{w}" data-height="{h}" data-duration="{giay}">
  <section class="clip" data-start="0" data-duration="{giay}" data-track-index="1">
    <svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
      {defs(M)}
      <rect width="{w}" height="{h}" fill="{M['bg']}"/>
      <rect width="{w}" height="{h}" fill="#000000" opacity="0.16"/>
      <rect width="{w}" height="{h}" fill="url(#leak)"/>
      <g opacity="0.25" filter="url(#tornS)">
        <rect x="{int(w*0.06)}" y="{int(h*0.09)}" width="90" height="60" fill="{CREAM}" transform="rotate(-18 {int(w*0.06)} {int(h*0.09)})"/>
        <rect x="{int(w*0.86)}" y="{int(h*0.88)}" width="110" height="70" fill="{M['accent']}" transform="rotate(12 {int(w*0.86)} {int(h*0.88)})"/>
        <rect x="{int(w*0.07)}" y="{int(h*0.84)}" width="70" height="90" fill="{M['pop']}" transform="rotate(24 {int(w*0.07)} {int(h*0.84)})"/>
      </g>
      <rect width="{w}" height="{h}" fill="url(#vig)"/>
      {svg}
      <rect width="{w}" height="{h}" filter="url(#grain)" opacity="0.55" pointer-events="none"/>
    </svg>
  </section>
</div>
<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["broll"] = tl;
</script>
</body></html>"""


def go_luong_tieng(f):
    """Canh tram phai CAM. Chep luong hinh, khong ma hoa lai."""
    try:
        co = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                             "-show_entries", "stream=index", "-of", "csv=p=0", f],
                            capture_output=True, timeout=120)
        if not co.stdout.strip():
            return
        tam = f + ".tam.mp4"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-c", "copy", "-an", tam],
                           capture_output=True, timeout=600)
        if r.returncode == 0 and os.path.isfile(tam):
            os.replace(tam, f)
        elif os.path.isfile(tam):
            os.remove(tam)
    except Exception:
        pass


def do_file(f):
    """Do file that bang ffprobe - khong tin 'render xong la dung'."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
             "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
             "-of", "json", f], capture_output=True, timeout=300)
        v = json.loads(r.stdout.decode("utf-8", "ignore"))["streams"][0]
        rate = v.get("r_frame_rate", "0/1").split("/")
        a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                            "-show_entries", "stream=index", "-of", "csv=p=0", f],
                           capture_output=True, timeout=120)
        return {"so_khung": int(v.get("nb_read_frames", 0)),
                "fps": round(float(rate[0]) / float(rate[1] or 1), 3),
                "rong": int(v.get("width", 0)), "cao": int(v.get("height", 0)),
                "co_tieng": bool(a.stdout.strip())}
    except Exception:
        return None


def lam_mot(yc, fps, khung, thu_muc, idx, da_mau, da_canh, video_goc=None, xem_truoc=False):
    loi = (yc.get("loi") or "").strip()

    # --- DO DAI: khop tung khung hinh ---
    if "bat_dau" in yc and "ket_thuc" in yc:
        giay = float(yc["ket_thuc"]) - float(yc["bat_dau"])
    elif "giay" in yc:
        giay = float(yc["giay"])
    else:
        sys.exit(f"[Cảnh {idx}] Chưa biết cảnh này dài bao nhiêu giây. "
                 f"Hãy nói rõ độ dài, ví dụ: dài 3 giây.")
    if giay <= 0:
        sys.exit(f"[Cảnh {idx}] Độ dài phải lớn hơn 0 giây (đang nhận {giay}).")

    f = int(yc.get("fps", fps))
    # LUAT CUNG: so khung = lam tron(giay x fps).
    # - KHONG dung round(): round() cua Python lam tron ve so chan (62.5 -> 62).
    # - Cong them epsilon: so thap phan trong may tinh khong tron tuyet doi
    #   (4.1*25 = 102.49999... chu khong phai 102.5) nen thieu epsilon thi
    #   ket qua doi theo sai so, khong doan truoc duoc.
    so_khung = max(1, int(giay * f + 0.5 + 1e-9))
    giay_that = so_khung / f          # HyperFrames tinh theo GIAY -> dua giay khop khung

    k = yc.get("khung", khung)
    if k not in KHUNG:
        sys.exit(f"[Cảnh {idx}] Không có khung hình '{k}'. "
                 f"Chọn một trong: {', '.join(KHUNG)} (dọc, ngang, vuông).")
    w, h = KHUNG[k]

    # --- MAU ---
    mau = dict(MAU_MAC_DINH)
    mau.update(chon_mau(loi, da_mau))
    if video_goc and "bat_dau" in yc:
        m = tong_mau_tu_video(video_goc, float(yc["bat_dau"]))
        if m:
            mau["bg"] = m
    for kh, key in (("mau_nen", "bg"), ("mau_nhan", "accent"), ("mau_chot", "pop")):
        if yc.get(kh):
            mau[key] = yc[kh]
    da_mau.append(mau["bg"])

    # --- CANH ---
    canh = yc.get("canh") or chon_canh(loi, da_canh)
    da_canh.append(canh)

    ten = yc.get("ra") or os.path.join(thu_muc, f"broll-{idx:02d}.mp4")
    ten = os.path.abspath(ten)
    os.makedirs(os.path.dirname(ten) or ".", exist_ok=True)

    # --- DUNG DU AN TAM + RENDER BANG HYPERFRAMES ---
    duan = tempfile.mkdtemp(prefix="broll-")
    try:
        # GSAP dat NGAY TRONG du an, khong tai tu mang: may khong mang hoac
        # mang cham la hong ca ban render, ma loi kieu do rat kho doan.
        if not os.path.isfile(GSAP):
            sys.exit("Thiếu phần làm động của xưởng.\n"
                     "Hãy cài lại xưởng bằng bộ cài của lớp là có.")
        shutil.copy2(GSAP, os.path.join(duan, "gsap.min.js"))
        with open(os.path.join(duan, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(dung_html(canh, round(giay_that, 4), w, h, mau))

        if xem_truoc:
            # snapshot ghi ra THU MUC (khong phai 1 file) -> chup vao thu muc tam
            # roi don dung tam anh cuoi ve dung ten nguoi goi yeu cau.
            ten = os.path.splitext(ten)[0] + ".png"
            kho = os.path.join(duan, "anh")
            cmd = ["npx", "hyperframes", "snapshot", duan, "-o", kho,
                   "--at", str(round(max(0.05, giay_that - 0.15), 3)),
                   "--no-end", "--describe", "false"]
            r = subprocess.run(cmd, capture_output=True, shell=True, timeout=900)
            ds_anh = sorted(
                (os.path.join(kho, x) for x in os.listdir(kho)) if os.path.isdir(kho) else [],
                key=os.path.getmtime)
            if r.returncode != 0 or not ds_anh:
                loi_txt = (r.stderr or r.stdout or b"").decode("utf-8", "ignore")[-700:]
                sys.exit(f"[Cảnh {idx}] Không tạo được ảnh xem trước.\n{loi_txt}")
            shutil.copy2(ds_anh[-1], ten)
        else:
            cmd = ["npx", "hyperframes", "render", duan, "-o", ten,
                   "-f", str(f), "--quiet"]
            r = subprocess.run(cmd, capture_output=True, shell=True, timeout=1800)
            if r.returncode != 0 or not os.path.exists(ten):
                loi_txt = (r.stderr or r.stdout or b"").decode("utf-8", "ignore")[-700:]
                sys.exit(f"[Cảnh {idx}] Không dựng được cảnh này.\n{loi_txt}")
    finally:
        shutil.rmtree(duan, ignore_errors=True)

    if xem_truoc:
        return {"stt": idx, "loi": loi, "file": ten, "xem_truoc": True,
                "canh": canh, "khung": k, "mau_nen": mau["bg"]}

    go_luong_tieng(ten)

    # --- TU KIEM (R17): do file that ---
    do = do_file(ten)
    canh_bao = []
    if do:
        if do["so_khung"] != so_khung:
            canh_bao.append(f"so khung lech: yeu cau {so_khung}, file co {do['so_khung']}")
        if abs(do["fps"] - f) > 0.05:
            canh_bao.append(f"fps lech: yeu cau {f}, file co {do['fps']}")
        if (do["rong"], do["cao"]) != (w, h):
            canh_bao.append(f"kich thuoc lech: yeu cau {w}x{h}, file co {do['rong']}x{do['cao']}")
        if do["co_tieng"]:
            canh_bao.append("file CO tieng - canh tram phai cam")
    else:
        canh_bao.append("khong do duoc bang ffprobe (thieu ffmpeg?)")
    for c in canh_bao:
        print(f"  [Cảnh {idx}] {c}", file=sys.stderr)

    return {"stt": idx, "loi": loi, "file": ten,
            "giay": round(so_khung / f, 4), "so_khung": so_khung, "fps": f,
            "khung": k, "canh": canh, "dat_chuan": not canh_bao, "canh_bao": canh_bao,
            "mau_nen": mau["bg"], "bat_dau": yc.get("bat_dau"), "ket_thuc": yc.get("ket_thuc")}


def main():
    p = argparse.ArgumentParser(
        description="Sinh canh tram B-roll cat dan giay bang HyperFrames. Skill chinh goi, tu ghep.")
    p.add_argument("--bang", help="File JSON nhieu yeu cau (khuyen dung)")
    p.add_argument("--loi", help="Cau thoai tai cho tram (che do 1 canh)")
    p.add_argument("--giay", type=float, help="Do dai canh tram (giay)")
    p.add_argument("--bat-dau", type=float, help="Moc bat dau tren video chinh")
    p.add_argument("--ket-thuc", type=float, help="Moc ket thuc tren video chinh")
    p.add_argument("--fps", type=int, default=30, help="PHAI bang fps video chinh (mac dinh 30)")
    # KHONG dung choices= : thu vien se bao loi bang tieng Anh kho hieu.
    # Tu kiem o duoi de bao bang tieng Viet.
    p.add_argument("--khung", default="9:16", help="Ti le khung: 9:16 | 16:9 | 1:1 | 4:5")
    p.add_argument("--ra", help="Duong dan file ra (che do 1 canh)")
    p.add_argument("--thu-muc", default="broll-out", help="Thu muc chua ca loat")
    p.add_argument("--tu-video", help="Video chinh: lay tong mau tai moc cho hop tone")
    p.add_argument("--mau-nen", help="Ep mau nen (vd #1b7d70)")
    p.add_argument("--canh", help="Ep an du hinh (xem --list-canh)")
    p.add_argument("--xem-truoc", action="store_true",
                   help="Chi ra ANH TINH de duyet (nhanh, re) - khong render video")
    p.add_argument("--list-canh", action="store_true", help="In danh sach an du hinh roi thoat")
    a = p.parse_args()

    if a.list_canh:
        print("CAC AN DU HINH CO SAN:\n")
        for ten, info in BANG_CANH:
            print(f"  {ten:<20} {info['y']}")
        print(f"\nMac dinh khi khong khop tu khoa nao: {CANH_MAC_DINH}")
        return

    if a.khung not in KHUNG:
        sys.exit(f"Không có khung hình '{a.khung}'.\n"
                 "Chọn một trong: 9:16 (dọc, cho Reels/TikTok) · 16:9 (ngang, cho YouTube) · "
                 "1:1 (vuông) · 4:5 (đứng, cho Facebook).")

    kiem_cong_cu()

    if a.bang:
        if not os.path.exists(a.bang):
            sys.exit(f"Không tìm thấy file danh sách yêu cầu: {a.bang}")
        with open(a.bang, "r", encoding="utf-8") as f:
            ds = json.load(f)
        if not isinstance(ds, list) or not ds:
            sys.exit("File danh sách yêu cầu phải có ít nhất một cảnh.")
    else:
        if not a.loi:
            sys.exit("Chưa có câu thoại. Hãy cho biết cảnh trám này minh hoạ cho câu nói nào.")
        mot = {"loi": a.loi}
        if a.bat_dau is not None and a.ket_thuc is not None:
            mot["bat_dau"], mot["ket_thuc"] = a.bat_dau, a.ket_thuc
        elif a.giay is not None:
            mot["giay"] = a.giay
        else:
            sys.exit("Chưa biết cảnh dài bao nhiêu. Cho biết số giây, hoặc mốc bắt đầu và kết thúc trên video chính.")
        for k, v in (("ra", a.ra), ("mau_nen", a.mau_nen), ("canh", a.canh)):
            if v:
                mot[k] = v
        ds = [mot]

    hop_le = [t for t, _ in BANG_CANH]
    for i, yc in enumerate(ds, 1):
        if yc.get("canh") and yc["canh"] not in hop_le:
            sys.exit(f"[Cảnh {i}] Không có ẩn dụ tên '{yc['canh']}'.\n"
                     f"Các ẩn dụ đang có: {', '.join(hop_le)}")

    ket_qua, da_mau, da_canh = [], [], []
    for i, yc in enumerate(ds, 1):
        # Chi bao tien do khi lam NHIEU canh; mot canh thi im lang cho gon mat.
        if len(ds) > 1:
            print(f"  Đang vẽ cảnh {i}/{len(ds)}: {yc.get('loi', '')[:55]}", file=sys.stderr)
        ket_qua.append(lam_mot(yc, a.fps, a.khung, a.thu_muc, i, da_mau, da_canh,
                               a.tu_video, a.xem_truoc))

    hong = [r for r in ket_qua if r.get("dat_chuan") is False]
    print(json.dumps({"so_canh": len(ket_qua), "dat_chuan_het": not hong, "canh": ket_qua},
                     ensure_ascii=False, indent=2))
    if hong:
        print(f"\n{len(hong)} cảnh chưa đạt chuẩn - xem mục 'canh_bao'. "
              "Đừng ghép vào video cho tới khi sửa xong.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
