# autovideo-master

Bộ công cụ tạo và sửa video qua một lệnh Python, AI điều phối bằng 6 skill. Bản kiểm thử 26/09/2026 [?].

## Cài trên Windows
Chạy trong PowerShell tại thư mục dự án:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\cai-dat.ps1
```
Nhập khóa vào `.env` trên máy; không dán khóa vào chat. Installer giữ `.env` và dữ liệu đang có, tạo môi trường Python riêng. Không cần Node hay script khóa học.

## Tạo video từ chữ
```powershell
.\.venv\Scripts\python.exe autovideo.py tao --kich-ban input\kich-ban-mau.txt --pixabay --khung 9:16
```
Lệnh in thư mục công việc mới trong `output/`. Mở `duyet-canh.md`, đọc 3 cảnh đề xuất mỗi đoạn. Trong `canh.json`, sao chép đối tượng ứng viên muốn dùng vào `selected`; để null khi không chèn cảnh. Có thể dùng ảnh/video cục bộ qua `selected: {"file": "D:/duong-dan/anh.jpg"}`. AI phải xem nội dung và chọn cảnh theo câu, không chỉ dựa vào thứ tự kết quả.
```powershell
.\.venv\Scripts\python.exe autovideo.py xuat --job "output/THU-MUC-CONG-VIEC" --duyet --kieu-chu vang-den
```
`--duyet` xác nhận các cảnh đã chọn. Chỉ cảnh được chọn mới được tải. Cảnh dùng lại được lưu tạm; không đóng gói video Pixabay gốc vào Git.

## Sửa video thật
Lệnh sau gửi riêng âm thanh đoạn được chỉ định lên Groq. AI phải có sự đồng ý của chủ video trước khi gửi nội dung riêng tư.
```powershell
.\.venv\Scripts\python.exe autovideo.py sua --video "D:/video.mp4" --tu 120 --do-dai 45
```
Xem `transcript.json`, sửa `words[].text` trong `job.json` nếu nhận sai; xem `diem-cat.json`, bật/tắt từng điểm cắt. Không tự bỏ các từ có thể mang nghĩa như “à”, “ừ”.
```powershell
.\.venv\Scripts\python.exe autovideo.py xuat --job "output/THU-MUC-CONG-VIEC" --duyet-cat
```
Muốn chèn B-roll vào video đã cắt: đặt `approved=true` trong `diem-cat.json`, chạy lần lượt `chuan-bi-canh --job ...`, `broll --job ...`, chọn cảnh rồi `xuat --job ... --duyet`. Thay điểm cắt phải tạo lại cảnh, kể cả khi tổng thời lượng không đổi.

## Phụ đề, ảnh và âm thanh
- 6 kiểu chữ: vang-den, trang-den, toi-gian, nen-den, karaoke, shorts. ASS hỗ trợ dấu tiếng Việt, mốc từng từ và xuống dòng ngắn.
- Ảnh cục bộ có chuyển động zoom nhẹ; video được căn theo thời gian giọng đọc, cắt/crop về khung 9:16 hoặc 16:9, tắt tiếng B-roll.
- Nhạc: `xuat ... --nhac "D:/nhac-co-quyen-dung.mp3"`; nhạc giảm âm lượng khi có giọng đọc.
- SFX: `--sfx input/sfx.json`, nội dung mẫu `[{"file":"D:/ting.wav","at":2.5,"volume":0.25}]`. Chỉ dùng âm thanh có quyền sử dụng đã xác nhận.
- `xuat` mã hóa H.264 CRF 20 một lần ở bước cuối, AAC, faststart. CRF có mất dữ liệu; không hứa tỷ lệ giảm dung lượng cố định. `nen` chỉ dành cho video có sẵn cần nén riêng.
- Không ghi đè thành phẩm; mỗi việc có thư mục riêng. `ket-qua.json` ghi thời lượng đo thực tế, phụ đề cuối và nguồn cảnh.

## Kiểm tra
```powershell
.\.venv\Scripts\python.exe autovideo.py kiem-tra
.\.venv\Scripts\python.exe tests/test-timeline.py
```
Kiểm thử thực tế 26/09/2026: kịch bản + Edge-TTS + 5 cảnh Pixabay, giọng 23.376s, video 23.367s, audio 23.376s; bài giảng thật đoạn 02:00–02:45, 141 từ, bỏ hai khoảng lặng còn video 43.000s / audio 42.990s. Đây là bản thử kỹ thuật chờ anh Lộc duyệt nội dung. Xem thêm `bao-cao-kiem-thu.md`.

## Giới hạn đã biết
Giọng Edge-TTS và Groq/Pixabay cần mạng, chịu hạn mức và điều khoản dịch vụ; không cam kết 0 đồng vĩnh viễn. Chưa tích hợp ElevenLabs, Pexels, phiên âm offline hay dựng collage nhiều lớp bằng HyperFrames. Bộ cốt lõi hiện dùng FFmpeg. Từ khóa và cảnh cần AI/người dùng kiểm tra theo nội dung. Bộ cài và xuất hàng loạt đã đạt kiểm thử native Windows/macOS trên GitHub Actions; xem bao-cao-bo-sung.md. K31 đã phiên âm cả buổi; nội dung chia bài chờ duyệt.

## Quyền sử dụng
Xem `NOTICE.md` và `CREDITS.md`. Script khóa học còn trong lịch sử Git, chưa có xác nhận quyền; không khôi phục, tự tải hoặc phân phối. 63 SFX và 7 BGM cũ giữ local, bỏ qua khi dựng mặc định. Không xóa lịch sử Git khi chưa có chỉ thị riêng.

Collage chia ô 2–4 ảnh/video: trong selected dùng files là danh sách đường dẫn local. Đã thử lưới 3 ảnh, giữ thời lượng video/audio 23.367s/23.376s. Hiệu ứng collage này dùng FFmpeg, không phải HyperFrames.

## Tách video dài theo nội dung
Dùng chung skill tach-video-theo-noi-dung cho bài học và clip ngắn, phần xử lý ở tach-video.py. AI đọc nội dung để lập bảng; mã kiểm tra mốc và xuất hàng loạt, lưu tiến độ và phục hồi lỗi. Bài học giữ khung gốc, phụ đề rời; clip ngắn có lựa chọn 9:16/16:9/gốc. Xem huong-dan-su-dung-ai.md để cài Windows/macOS và ra lệnh bằng tiếng Việt trong Codex/Claude Code/Antigravity/Cursor.
