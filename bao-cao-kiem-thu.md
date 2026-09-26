# Báo cáo kiểm thử 26/09/2026 [?]

1. Tạo từ input/kich-ban-mau.txt: Edge-TTS + 5 clip Pixabay; audio 23.376s, video 23.366667s, container 23.376s, phụ đề cuối 22.5375s; 720×1280, 6.69MB. Kiểm tra một khung hình có chữ tiếng Việt và cảnh AI hiển thị đúng. Cảnh được chọn cho thử kỹ thuật, chưa phải duyệt biên tập của anh Lộc.
2. Sửa video ĐSCH K31 - B3.mp4: chỉ đoạn 02:00–02:45 theo sự đồng ý của anh. Groq nhận 141 từ. Hai khoảng lặng 6.702063–7.677688 và 22.459813–23.494500; tổng bỏ 2.010312s. Thành phẩm video 43.000s, audio 42.989688s, phụ đề cuối 42.849688s; 720×450, 1.13MB. Xem khung hình ở giây 20, phụ đề có dấu và nằm trong khung.
3. 5 kiểm thử logic đạt: cảnh liên tục hết audio, gộp cắt chồng nhau, chuyển mốc từ sau cắt, giới hạn phụ đề, từ chối cắt hết/điểm không hợp lệ và làm tròn thời gian.
4. Khóa cục bộ có mặt; không đưa khóa vào mã, báo cáo hoặc commit. Mạng bị chặn thì báo lỗi, không giả kết quả. Không dùng mẫu TTS để thay bài giảng thật.

Chưa nghe đánh giá nghệ thuật toàn bộ hai file; chưa thử đầy đủ bài giảng 102 phút; macOS/Linux chưa thử native. Chi tiết installer được bổ sung sau lượt kiểm tra sạch.

5. Installer Windows đã chạy ở thư mục trống autovideo-clean-install: tạo .venv, cài 16 phụ thuộc, tải FFmpeg/ffprobe vào bin, lệnh kiem-tra errors=[] với .env rỗng; chưa phải kiểm thử Windows không cài sẵn Python/uv.
6. Dùng chính .venv và FFmpeg của bản cài sạch xuất 16:9, ảnh local zoom, karaoke, nhạc tone tự tạo + SFX; video 23.366667s/audio 23.376s. Kiểm tra thực thi và thời lượng; chưa đánh giá cân bằng âm thanh bằng tai.

7. Bản cài D:/autovideo-master: kiem-tra errors=[], cả hai khóa có mặt; 15 SKILL.md (5 bản chính và liên kết riêng cho Claude/Codex) qua quick_validate. Xuất lại bài giảng bằng .venv và bin của dự án: video 43.000s/audio 42.989688s, file video-kiem-tra-ban-cai.mp4, 1.41MB. Không gửi thêm âm thanh lên dịch vụ.

8. Collage lưới 3 ảnh bằng FFmpeg: xuất 360×640, video 23.366667s/audio 23.376s; kiểm thử bố cục cơ bản, chưa phải hiệu ứng xé giấy/chồng lớp.
