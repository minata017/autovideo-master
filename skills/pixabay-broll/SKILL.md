---
name: pixabay-broll
description: Tìm video Pixabay theo từng đoạn, đề xuất lựa chọn và chèn B-roll vào video tạo hoặc sửa.
---

# pixabay-broll

Đọc README.md và NOTICE.md. Khóa PIXABAY_API_KEY nằm trong .env; không in ra chat.
Chạy autovideo.py broll --job DIR. API cache 24 giờ, không hỗ trợ tham số orientation cho videos. Kiểm tra width/height thật của ứng viên.
Xem duyet-canh.md, chọn cảnh theo nội dung câu. Ghi một đối tượng candidates vào selected hoặc {"file":"đường dẫn tuyệt đối"} cho video/ảnh local. null để giữ hình gốc/nền.
Không chọn chỉ vì đứng đầu kết quả. Chỉ tải cảnh được chọn khi xuat --job DIR --duyet; thời gian overlay căn theo start/end của canh.json. Sau đổi điểm cắt phải tạo lại cảnh.
Lưu nguồn trong ket-qua.json; không phân phối kho clip gốc. Không hứa Pixabay Audio có API tích hợp.
