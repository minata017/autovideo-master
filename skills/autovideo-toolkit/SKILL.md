---
name: autovideo-toolkit
description: Tạo video từ kịch bản hoặc sửa video thô, phiên âm, đề xuất cắt và xuất thành phẩm bằng autovideo.py.
---

# autovideo-toolkit

Đọc README.md. Dùng .venv/Scripts/python.exe trên Windows, .venv/bin/python trên macOS/Linux.
Tạo: tao --kich-ban FILE --pixabay --khung 9:16 hoặc 16:9.
Sửa: sua --video FILE [--tu GIAY --do-dai GIAY]. Có đồng ý trước khi gửi nội dung riêng tư lên Groq.
Đọc transcript.json và job.json; sửa chữ nhận sai trong words của job.json. Xem diem-cat.json trước khi dùng xuat --job DIR --duyet-cat. B-roll cho video sửa phải chạy chuan-bi-canh sau khi duyệt cắt rồi broll.
Xuat mã hóa một lần; kiểm tra ket-qua.json và thành phẩm. Không khôi phục script khóa học. Không nhận xét đã nghe tiếng nếu chưa nghe.
