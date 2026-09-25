# Cài đặt - dành cho người nhận chuyển giao

Bộ công cụ này chạy độc lập, không dính vào một hãng AI nào. Cài xong dùng được với
Claude, ChatGPT, Gemini, Cursor, hay chạy tay bằng lệnh.

## Bước 1 - Cài 2 thứ

**Node.js 18 trở lên** - https://nodejs.org (bản LTS)
Kiểm: `node --version` -> phải ra `v18` trở lên.

**ffmpeg** - https://ffmpeg.org/download.html
- Windows: tải bản `essentials`, giải nén, thêm thư mục `bin` vào PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

Kiểm: `ffmpeg -version` -> phải thấy dòng có chữ `libass`.
Không có `libass` thì không nướng được phụ đề, phải tải bản khác.

## Bước 2 - Chép thư mục này về máy

Đặt ở đâu cũng được. Ví dụ `D:\cong-cu\tao-kieu-chu-caption` hay `~/tao-kieu-chu-caption`.

## Bước 3 - Chuẩn bị font

Kiểu chữ mẫu đi kèm dùng font **Segoe UI** (có sẵn trên Windows). Máy khác thì thả
file font vào thư mục `fonts/` rồi sửa tên font trong file kiểu chữ.

Font tiếng Việt miễn phí dùng được cho cả mục đích thương mại:
- **Be Vietnam Pro**, **Montserrat**, **Roboto**, **Inter** - tải ở Google Fonts

Tải cả họ font (Regular, Bold, Black...) chứ đừng tải một file, vì mỗi độ đậm là một
file riêng.

Kiểm font trước khi dùng:

```bash
node scripts/caption.mjs kiem-font fonts/BeVietnamPro-Bold.ttf
```

Phải ra `Dấu tiếng Việt: ĐỦ`. Ra `THIẾU` thì đừng dùng font đó cho phụ đề tiếng Việt.

## Bước 4 - Chạy thử

```bash
node scripts/tu-kiem.mjs
```

Ra `KẾT QUẢ: 20 đạt · 0 hỏng` là cài xong.

## Bước 5 - Nối vào AI đang dùng

**Claude Code / Claude Desktop**: chép cả thư mục vào `~/.claude/skills/`. Xong.

**AI khác (ChatGPT, Gemini, Cursor...)**: dán đoạn dưới vào phần chỉ dẫn của trợ lý,
sửa lại đường dẫn cho đúng máy mình:

```
Khi người dùng cần làm phụ đề cho video, đổi kiểu chữ phụ đề, hay tạo kiểu chữ
phụ đề riêng, hãy dùng bộ công cụ ở D:\cong-cu\tao-kieu-chu-caption.
Đọc file SKILL.md ở đó để biết cách gọi, rồi chạy lệnh bằng terminal.
```

**Không có AI, tự chạy tay**: mở terminal, đọc `SKILL.md`, gõ lệnh.

## Hay gặp

**"Không tìm thấy font ..."** - font chưa cài hoặc chưa thả vào `fonts/`.
Lỗi in ra sẵn danh sách thư mục máy đã tìm.

**"ffmpeg is not recognized"** - chưa thêm ffmpeg vào PATH. Cài lại theo Bước 1.

**Phụ đề tràn 2 dòng** - chạy `node scripts/caption.mjs chuan-co` để đo lại cỡ chữ.
Đổi font xong luôn phải chạy lệnh này.

**Chữ mất dấu, ra ô vuông** - font thiếu dấu tiếng Việt. Chạy `kiem-font` để xác nhận,
rồi đổi font khác.
