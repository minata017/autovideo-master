# autovideo-master

Bộ công cụ dựng và biên tập video tự động bằng AI, hoạt động độc lập và điều khiển 100% bằng câu lệnh tiếng Việt tự nhiên trong chat. Tương thích toàn bộ các trợ lý AI (Codex, Antigravity, Claude, Cursor, Windsurf).

---

## 🚀 Cài đặt tự động 1 dòng lệnh

### Dành cho Windows (PowerShell):
```powershell
irm https://raw.githubusercontent.com/minata017/autovideo-master/main/cai-dat.ps1 | iex
```

### Dành cho macOS / Linux (Terminal):
```bash
curl -fsSL https://raw.githubusercontent.com/minata017/autovideo-master/main/cai-dat.sh | bash
```

---

## ⚙️ Cấu hình ban đầu

1. Sau khi cài đặt, mở file `.env` tại thư mục gốc:
```bash
GROQ_API_KEY=your_groq_api_key_here
```
*(Lấy mã khóa Groq miễn phí tại [console.groq.com/keys](https://console.groq.com/keys) để bóc giọng nói siêu tốc trong 3-5 giây)*

2. Tùy chọn nâng cao:
   - `ELEVENLABS_API_KEY`: Dành cho giọng đọc thuyết minh có phí cao cấp.
   - `PEXELS_API_KEY`: Dành cho tìm kiếm video B-roll tự động miễn phí.

---

## 📂 Cấu trúc thư mục

```text
autovideo-master/
├── .env.example              # Mẫu cấu hình API
├── .env                      # File cấu hình cục bộ (chặn đưa lên Git)
├── .gitignore                # Bảo vệ an toàn mã khóa và dữ liệu
├── README.md                 # Hướng dẫn sử dụng
├── CREDITS.md                # Ghi công bản quyền nguồn mở (MIT, OFL, CC)
├── cai-dat.ps1               # Cài đặt tự động cho Windows
├── cai-dat.sh                # Cài đặt tự động cho macOS/Linux
├── CLAUDE.md                 # Nhạc trưởng cho Claude Code / Claude Desktop
├── AGENTS.md                 # Nhạc trưởng cho Codex, Antigravity, Cursor
├── bin/                      # Chứa FFmpeg độc lập
├── input/                    # Nơi thả video thô hoặc kịch bản
├── output/                   # Nơi nhận video thành phẩm (9:16 hoặc 16:9)
├── temp/                     # Thư mục xử lý tạm thời
└── skills/                   # 4 skill nghiệp vụ
    ├── autovideo-toolkit/    # Bóc lời Groq LPU, cắt "ờ à", jump-cut, nén CRF 20
    ├── kho-am-thanh/         # 63 SFX phân loại + 7 BGM Piano YouTube Audio Library
    ├── tao-kieu-chu-caption/ # 10 Font việt hóa OFL + 5 mẫu phụ đề nhảy chữ
    └── dung-broll-collage/   # Dựng cảnh B-roll ảnh chuyển động HyperFrames
```

---

## 🎬 Cách sử dụng

### 1. Sửa video người nói thô
1. Thả video vào `input/`.
2. Mở trợ lý AI (Claude, Antigravity, Codex) và ra lệnh:
   > *"Cắt lọc các đoạn ờ à, thêm phụ đề vàng đen và xuất video giúp anh"*
3. Nhận video thành phẩm đã được cắt sạch và tự động nén nét cao tại `output/`.

### 2. Tạo video từ kịch bản chữ
1. Thả file kịch bản `.txt` vào `input/` hoặc dán trực tiếp vào chat:
   > *"Tạo video ngắn 9:16 từ kịch bản này với giọng đọc truyền cảm"*
2. AI tự động lồng tiếng (Edge-TTS 0đ / ElevenLabs), ghép ảnh B-roll và dập chữ phụ đề.
3. Nhận video thành phẩm tại `output/`.

---

## 🔒 Bản quyền & Giấy phép

Toàn bộ các thành phần nguồn mở đi kèm được ghi nhận đầy đủ theo điều khoản giấy phép tại [CREDITS.md](CREDITS.md).
