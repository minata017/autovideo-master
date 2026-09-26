---
name: tao-kieu-chu-caption
description: Thêm phụ đề tiếng Việt căn theo giọng, chọn kiểu chữ vàng đen, karaoke hoặc chữ ngắn bằng ASS.
---

# tao-kieu-chu-caption

Dùng autovideo.py xuat --job DIR --kieu-chu STYLE.
Các STYLE: vang-den, trang-den, toi-gian, nen-den, karaoke, shorts. Chọn theo hình gốc và khoảng an toàn; kiểm tra không che thông tin quan trọng.
Mốc từng từ trong job.json dùng để tạo phu-de.srt và phu-de.ass; giới hạn dòng ngắn, không chạy script .mjs khóa học. Font trong fonts/ giữ nguyên giấy phép OFL.
Sửa chữ sai ở words[].text trong job.json trước xuất. Kiểm tra phụ đề cuối không vượt thời lượng và dấu tiếng Việt hiển thị đúng.
