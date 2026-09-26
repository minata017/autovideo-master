# Dùng cùng bộ công cụ với trợ lý AI

Mục tiêu hỗ trợ Windows và macOS. Bộ cài chuẩn bị Python riêng, FFmpeg và các thư viện; trợ lý AI sử dụng tài khoản/cài đặt sẵn của người dùng, có quyền đọc file và chạy lệnh cục bộ.

## Cài một dòng
Windows PowerShell:
```powershell
irm https://raw.githubusercontent.com/minata017/autovideo-master/main/cai-dat.ps1 | iex
```
macOS Terminal:
```bash
curl -fsSL https://raw.githubusercontent.com/minata017/autovideo-master/main/cai-dat.sh | bash
```
Piped installer mặc định ở thư mục autovideo-master trong thư mục người dùng. Tải repo về trước rồi chạy installer tại đó sẽ cài đúng thư mục repo. Giữ khóa trong .env của từng máy; không chuyển khóa vào Git. Mac có thể yêu cầu mật khẩu quản trị và Command Line Tools khi cài Homebrew/FFmpeg. Installer dừng khi thiếu công cụ, không báo thành công giả.

## Mở dự án trong AI
| Trợ lý | Hướng dẫn trong dự án |
|---|---|
| Codex | AGENTS.md và .agents/skills/ |
| Claude Code | CLAUDE.md và .claude/skills/ |
| Antigravity | AGENTS.md/GEMINI.md và .agents/skills/; bản cũ có thể đọc trực tiếp skill trong skills/ |
| Cursor | AGENTS.md, .cursor/rules/autovideo.mdc, các skill chính trong skills/ |

Mở thư mục autovideo-master làm dự án/workspace. Có thể cần mở lại phiên để ứng dụng nhận skill mới. Nếu ứng dụng chưa tự nhận, câu lệnh sau yêu cầu đọc file trực tiếp:
```text
Đọc AGENTS.md và README.md trong dự án autovideo-master, rồi dùng skill phù hợp để làm video theo yêu cầu của tôi. Dùng Python trong .venv; giữ video gốc và khóa API cục bộ.
```

## Tạo các bài học từ bản ghi
```text
Tách video này thành các bài học theo từng chủ đề. Giữ đủ lời giải thích, ví dụ và câu hỏi liên quan. Giữ khung hình tài liệu rõ. Hãy dùng skill tách video theo nội dung, lập bảng tên bài và đoạn giữ/bỏ để tôi duyệt trước khi xuất hàng loạt. Chỉ tạo video, phụ đề và danh mục file.
```
## Tạo clip ngắn từ video dài
```text
Tìm các đoạn có ý nghĩa trong video này để tạo clip ngắn xem độc lập. Giữ đủ ngữ cảnh và không cắt sai ý người nói. Đề xuất tiêu đề, mốc đầu-cuối và khung hình để tôi duyệt, rồi dùng skill tách video theo nội dung để xuất hàng loạt.
```

## Lệnh kỹ thuật khi cần
Windows dùng .venv/Scripts/python.exe, Mac dùng .venv/bin/python.
```text
python tach-video.py chuan-bi --video "DUONG-DAN-VIDEO"
python tach-video.py tiep-tuc --job "THU-MUC-CONG-VIEC"
python tach-video.py xem-ke-hoach --job "THU-MUC-CONG-VIEC"
python tach-video.py xuat --job "THU-MUC-CONG-VIEC" --duyet --muc-dich bai-hoc
```
Các lệnh Python trên là cú pháp minh họa, thay python bằng Python trong .venv. Không gửi nội dung riêng tư lên Groq trước khi có đồng ý đúng phạm vi.

## Nguồn hướng dẫn tích hợp
https://www.antigravity.google/docs/skills/ ; https://www.antigravity.google/docs/rules/ ; https://code.claude.com/docs/en/skills ; https://cursor.com/docs/rules . Cấu trúc file dựa theo tài liệu; không tuyên bố đã thao tác thử trực tiếp cả bốn ứng dụng.
