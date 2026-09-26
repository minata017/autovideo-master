---
name: dung-broll-collage
description: Chèn ảnh hoặc video minh họa cục bộ vào từng đoạn, crop khung và zoom ảnh nhẹ.
---

# dung-broll-collage

Dùng cùng canh.json như skill pixabay-broll. selected={"file":"đường dẫn ảnh hoặc video"}, start/end là mốc trên video xuất.
Chạy autovideo.py xuat --job DIR --duyet. Ảnh jpg/png/webp có zoom nhẹ; video crop vào khung và lặp nếu ngắn.
Collage 2–4 ảnh/video dạng chia ô: selected={"files":["D:/anh-1.jpg","D:/anh-2.jpg"]}. Hai file chia hai cột; 3–4 file chia lưới 2×2, ô thiếu màu đen. Căn theo thời lượng đoạn, tắt tiếng video minh họa. Chưa có xé giấy, chồng lớp tự do hoặc HyperFrames; không gọi script khóa học để lấp thiếu.
