---
name: kho-am-thanh
description: Phối nhạc nền và hiệu ứng âm thanh cục bộ đã có quyền sử dụng, giảm nhạc khi có giọng.
---

# kho-am-thanh

Dùng autovideo.py xuat --job DIR --nhac FILE, hoặc --sfx FILE_JSON.
JSON hiệu ứng: [{"file":"D:/ting.wav","at":2.5,"volume":0.25}]. Mốc at tính trên video sau cắt.
Nhạc lặp và fade, giảm âm lượng theo giọng qua sidechain; tiếng B-roll bị tắt.
Không tự dùng 63 SFX/7 BGM cũ vì quyền từng file chưa xác minh. Hỏi nguồn hoặc dùng file người dùng xác nhận quyền; không phân phối file gốc. Nghe lại kết quả trước khi nhận xét độ cân bằng.
