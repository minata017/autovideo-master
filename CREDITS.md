# Nguồn, quyền sử dụng và ghi công

Cập nhật 26/09/2026. Không tuyên bố an toàn pháp lý tuyệt đối.

## Bản vận hành hiện tại
- autovideo.py, wrapper, installer và hướng dẫn mới được viết trong phiên hoàn thiện, không gọi mã script khóa học. Repo chưa đặt giấy phép phân phối riêng cho mã tự viết; không tự gán MIT cho toàn bộ dự án.
- Edge-TTS: rany2, MIT, https://github.com/rany2/edge-tts . Requests: Apache 2.0, https://requests.readthedocs.io/ . Cài qua pip; giữ giấy phép trong gói.
- uv: Astral, MIT/Apache-2.0, https://docs.astral.sh/uv/ . Tải từ nguồn chính thức.
- FFmpeg/ffprobe: https://ffmpeg.org/legal.html ; quyền phụ thuộc cấu hình build. Windows tải từ gyan.dev hoặc dùng binary sẵn có; binary không commit vào repo.
- Groq: gọi HTTP API phiên âm; chịu điều khoản/hạn mức dịch vụ, không đóng gói model. Pixabay: cảnh tải theo giấy phép nội dung https://pixabay.com/service/license-summary/ ; lưu nguồn từng clip trong ket-qua.json, không phân phối lại kho nguyên liệu gốc.
- Core mới không cài hoặc gọi HyperFrames, GSAP, video-use, yt-dlp hay SDK Groq.

## Font đi kèm
Be Vietnam Pro, Barlow Condensed, Montserrat, Fira Sans, Mulish, Open Sans: giữ các file GIAY-PHEP-*-OFL.txt trong skills/tao-kieu-chu-caption/fonts/. Open Sans trong bản này có SIL OFL 1.1 theo file đi kèm, đã sửa nhận định Apache 2.0 của báo cáo cũ. Phải giữ notice khi phân phối font.

## Tài nguyên cũ
21 script Lê Thanh Sơn dành cho khóa Autovideo từng có trong lịch sử Git; chưa xác nhận quyền phân phối. Installer mới không tự tải; không khôi phục. Xem NOTICE.md.
63 SFX và 7 BGM cũ chưa xác minh từng file, giữ local, không phân phối hoặc dùng mặc định. Các cấu hình/hiệu ứng từ bản cũ không được core mới gọi; không xem repo công khai là bằng chứng giấy phép.
