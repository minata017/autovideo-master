---
name: pixabay-broll
description: Tim, tai va chen video B-roll tu Pixabay vao video chinh. Ho tro 9:16 va 16:9, doc PIXABAY_API_KEY tu .env, loc theo resolution thuc te (khong gia dinh), xuat danh sach canh cho nguoi dung duyet truoc khi ghep.
---

# pixabay-broll - Tim & chen video B-roll tu Pixabay

## 1. Tong quan

Skill nay giup AI tu dong tim kiem video B-roll phu hop tren Pixabay.com dua tren noi dung tung doan thoai, tai ve, cat dung do dai va chen vao video chinh.

## 2. Yeu cau

- File `.env` phai chua `PIXABAY_API_KEY=<khoa>` (lay mien phi tai https://pixabay.com/api/docs/)
- Python 3.10+, thu vien `requests` (da cai qua pip)
- FFmpeg co trong PATH

## 3. Cach su dung

### Buoc 1: Chuan bi danh sach canh can B-roll

Tao file JSON `temp/canh-can-broll.json`:
```json
[
  {"cau": "Cong nghe dang thay doi the gioi", "start": 0.0, "end": 5.2, "keyword_goi_y": "technology"},
  {"cau": "Nhung khu rung nhiet doi dang bien mat", "start": 5.2, "end": 10.8, "keyword_goi_y": "tropical forest"}
]
```

### Buoc 2: Chay script tim B-roll

```bash
python skills/pixabay-broll/scripts/tim-broll.py \
  --canh temp/canh-can-broll.json \
  --khung 9:16 \
  --output temp/broll-de-xuat.json
```

### Buoc 3: Duyet danh sach de xuat

Script xuat bang de xuat gom: STT, cau thoai, keyword, video Pixabay (ID, link, resolution, thoi luong), vi tri chen (start-end giay). **Nguoi dung duyet truoc khi tai.**

### Buoc 4: Tai va cat video

```bash
python skills/pixabay-broll/scripts/tim-broll.py \
  --canh temp/canh-can-broll.json \
  --khung 9:16 \
  --duyet temp/broll-de-xuat.json \
  --tai \
  --output temp/broll/
```

## 4. Logic xu ly khung hinh

- **9:16 (doc):** Tim video co `height > width`. Neu khong co -> lay video ngang, crop giua.
- **16:9 (ngang):** Tim video co `width > height`. Neu khong co -> lay video doc, them nen mo 2 ben.
- **Chon resolution:** Duyet `large` -> `medium` -> `small` -> `tiny`, chon ban >= 720p gan nhat voi muc tieu. KHONG gia dinh ban nao la 1080p.

## 5. Fallback

Neu Pixabay khong tim duoc canh phu hop (0 hits hoac keyword qua hep):
1. Thu tim voi keyword rong hon (bỏ tính từ, giữ danh từ chính)
2. Bao cho nguoi dung va goi y dung file trong `input/broll/`

## 6. Giay phep Pixabay

- Dung thuong mai: **Co**
- Chen vao video moi: **Co**
- Ghi cong: **Khong bat buoc** (nhung khuyen khich)
- Ban lai video goc: **Cam**
- Link nguon duoc ghi vao `temp/broll-sources.json`

## 7. Tich hop voi 2 quy trinh

### QT1 (sua video tho):
AI phan tich transcript -> tim doan can B-roll -> goi skill nay -> chen canh minh hoa

### QT2 (tao video tu kich ban):
AI chia kich ban thanh cac doan -> goi skill nay tim canh cho tung doan -> ghep B-roll + voiceover + phu de
