---
name: autovideo-toolkit
description: Bộ công cụ cắt gọt video thông minh, bóc lời thoại tiếng Việt bằng Groq Whisper LPU siêu tốc, phát hiện và cắt bỏ từ đệm "ờ, à", cắt bỏ đoạn ngập ngừng (jump-cut), chia clip và tự động nén video chuẩn CRF 20 tối ưu dung lượng không mất nét.
---

# autovideo-toolkit - Cắt lọc, Phiên âm & Nén video

Tập hợp các script thực thi cốt lõi nằm trong `skills/autovideo-toolkit/scripts/`.

## 1. Các công cụ chính

1. **Phiên âm siêu tốc (`transcribe_groq.py`):**
   - Trích xuất audio từ video và gửi lên Groq Cloud LPU.
   - Model mặc định: `whisper-large-v3-turbo` (hoặc `whisper-large-v3`).
   - Kết quả: File JSON chứa transcript chi tiết từng từ kèm mốc thời gian bắt đầu và kết thúc (word-level timestamps).

2. **Dò từ đệm & đoạn ngập ngừng (`tim_tu_dem.py`):**
   - Phân tích transcript JSON để tìm:
     - Đoạn lặng, khoảng dừng ngắc ngứ > 0.5 giây.
     - Các từ đệm thừa: "ờ", "à", "ừm", "kiểu như là", "thì là mà".
   - Xuất danh sách các điểm cần cắt bỏ vào file `diem-cat.json`.

3. **Cắt gọt không suy hao (`cat_video.py`):**
   - Thực thi cắt bỏ các đoạn đã chọn theo danh sách `diem-cat.json`.
   - Cơ chế: Cắt và ghép trực tiếp bằng FFmpeg stream copy, chèn 30ms audio fade ở mép cắt để chống tiếng "pop" giật.

4. **Nén video tối ưu (`nen-video.py`):**
   - Nén video thành phẩm bằng FFmpeg H.264 với CRF 20, preset slow, web-optimized.
   - Mục tiêu: Giảm dung lượng 50-75% so với file thô/CapCut mà mắt thường không phân biệt được suy giảm chất lượng.
   - Tự động chạy ở bước cuối cùng trước khi đưa video vào `output/`.

5. **Các tiện ích khác:**
   - `chia_clip.py`: Tách 1 video dài thành nhiều clip ngắn theo chủ đề.
   - `tai_video.py`: Tải video tham khảo từ link YouTube/TikTok/Facebook qua yt-dlp.
   - `lam_thumbnail.py`: Tự động trích xuất khung hình đẹp làm ảnh bìa.

## 2. Quy trình phối hợp chuẩn khi sửa video người nói

```bash
# Bước 1: Bóc lời thoại
python scripts/transcribe_groq.py input/video.mp4 -o temp/transcript.json

# Bước 2: Dò tìm từ đệm và đoạn lặng
python scripts/tim_tu_dem.py temp/transcript.json -o temp/diem-cat.json

# Bước 3: Cắt gọt video thô
python scripts/cat_video.py input/video.mp4 --diem-cat temp/diem-cat.json -o temp/video-da-cat.mp4

# Bước 4: (Gắn phụ đề & SFX theo skill tương ứng)

# Bước 5: Nén tối ưu xuất ra output
python scripts/nen-video.py temp/video-hoan-thien.mp4 -o output/video-thanh-pham.mp4
```
