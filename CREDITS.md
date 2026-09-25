# Bảng nguồn, giấy phép & yêu cầu ghi công

Bộ công cụ **autovideo-master** tích hợp nhiều thành phần từ nhiều nguồn khác nhau. Bảng dưới đây ghi rõ giấy phép, yêu cầu ghi công và trạng thái xác minh cho từng thành phần.

---

## 1. Công cụ phần mềm (cài qua script, KHÔNG đóng gói trong repo)

| Thành phần | Tác giả | Giấy phép | Yêu cầu ghi công | Cách tích hợp | Trạng thái |
|---|---|---|---|---|---|
| FFmpeg & ffprobe | FFmpeg Team | LGPL 2.1 / GPL | Giữ nguyên LICENSE khi phân phối binary | Script `cai-dat.ps1` tải từ gyan.dev, không đóng gói | ✅ Xác minh |
| uv | Astral | MIT / Apache-2.0 | Giữ nguyên notice | Script tải từ astral.sh | ✅ Xác minh |
| yt-dlp | yt-dlp Team | The Unlicense (Public Domain) | Không yêu cầu | Cài qua `uv tool install` | ✅ Xác minh |
| HyperFrames | HeyGen | npm package (proprietary) | Không phân phối lại source | Cài qua `npm install -g` | ✅ Xác minh |
| GSAP | GreenSock | Standard "No-Charge" License | Không được đóng gói vào repo; phải cài qua npm hoặc CDN | Đã loại khỏi repo; HyperFrames tự kéo | ✅ Đã sửa |
| video-use | Browser Use | MIT License | Giữ nguyên dòng bản quyền gốc trong file LICENSE | Script cài đặt clone từ kho gốc | ✅ Xác minh |
| Edge-TTS | rany2 | MIT License | Giữ attribution | Cài qua pip | ✅ Xác minh |
| groq (Python SDK) | Groq Inc | Apache 2.0 | Giữ attribution | Cài qua pip | ✅ Xác minh |

## 2. Script do Lê Thanh Sơn viết (Khóa Autovideo)

| Nhóm | Số file | Bản quyền gốc | Giấy phép rõ ràng? | Hành động |
|---|---|---|---|---|
| `viet-hoa/` (10 file .py) | 10 | "phát hành cho học viên khóa Autovideo" | ❌ KHÔNG có file LICENSE, KHÔNG có điều khoản phân phối lại | **ĐÃ LOẠI KHỎI REPO** |
| `kieu-chu-caption/scripts/` (9 file .mjs) | 9 | Thuộc repo `sontyphu/autovideo-effects` | ❌ Không có giấy phép nguồn mở | **ĐÃ LOẠI KHỎI REPO** |
| `broll-collage/scripts/` (2 file .py) | 2 | Thuộc repo `sontyphu/autovideo-effects` | ❌ Không có giấy phép nguồn mở | **ĐÃ LOẠI KHỎI REPO** |

**Giải pháp thay thế:** Script cài đặt (`cai-dat.ps1` / `cai-dat.sh`) sẽ tải các script này trực tiếp từ repo gốc `sontyphu/autovideo-toolkit` và `sontyphu/autovideo-effects` tại thời điểm cài đặt — đúng như cách repo gốc thiết kế ("bộ cài tải thẳng từ kho gốc"). Repo `autovideo-master` chỉ chứa file SKILL.md hướng dẫn AI cách gọi, không chứa mã nguồn.

## 3. Kiểu chữ (Fonts) — ĐI KÈM trong repo

| Font | Tác giả | Giấy phép | Yêu cầu | File giấy phép đi kèm | Trạng thái |
|---|---|---|---|---|---|
| Be Vietnam Pro | Fábrica Team | SIL OFL 1.1 | Giữ nguyên file OFL.txt | `GIAY-PHEP-BeVietnamPro-OFL.txt` | ✅ Có |
| Barlow Condensed | Jeremy Tribby | SIL OFL 1.1 | Giữ nguyên file OFL.txt | `GIAY-PHEP-BarlowCondensed-OFL.txt` | ✅ Có |
| Montserrat | Julieta Ulanovsky | SIL OFL 1.1 | Giữ nguyên file OFL.txt | `GIAY-PHEP-Montserrat-OFL.txt` | ✅ Có |
| Fira Sans | Carrois / Edenspiekermann | SIL OFL 1.1 | Giữ nguyên file OFL.txt | `GIAY-PHEP-FiraSans-OFL.txt` | ✅ Có |
| Mulish | Vernon Adams | SIL OFL 1.1 | Giữ nguyên file OFL.txt | `GIAY-PHEP-Mulish-OFL.txt` | ✅ Có |
| Open Sans | Steve Matteson | Apache 2.0 | Giữ nguyên file OFL.txt | `GIAY-PHEP-OpenSans-OFL.txt` | ✅ Có |

## 4. Hiệu ứng âm thanh (SFX) — ĐI KÈM trong repo

| Nhóm | Số file | Nguồn gốc ghi trong repo gốc | Giấy phép | Trạng thái xác minh |
|---|---|---|---|---|
| 63 SFX (đóng gói từ `sontyphu/autovideo-effects/sfx/`) | 63 | Repo gốc KHÔNG ghi rõ nguồn từng file. File `00-CACH-DUNG.md` ghi "anh Sơn chốt 14/08/2026", tên file gợi ý các nguồn phổ biến (whoosh, pop, ting — phong cách YouTube Audio Library / Freesound) nhưng KHÔNG có bằng chứng giấy phép cụ thể cho từng file. | ⚠️ **CHƯA XÁC MINH TỪNG FILE** | Giữ lại tạm thời vì đi kèm repo công khai; ghi chú cần hỏi tác giả gốc |

## 5. Nhạc nền (BGM) — ĐI KÈM trong repo

| Bản nhạc | Nghệ sĩ | Nguồn | Giấy phép | Trạng thái |
|---|---|---|---|---|
| Angel's Dream | Aakash Gandhi | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận trên YouTube Audio Library |
| Invisible Beauty | Aakash Gandhi | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận |
| Just Stay | Aakash Gandhi | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận |
| The Beauty of Love | Aakash Gandhi | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận |
| No.2 Remembering Her | Esther Abrami | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận |
| No.6 In My Dreams | Esther Abrami | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận |
| Forever Yours | Wayne Jones | YouTube Audio Library | Miễn phí, không yêu cầu ghi công | ⚠️ Cần xác nhận |

## 6. Script do autovideo-master tự viết — CÓ trong repo

| File | Mô tả | Tác giả | Giấy phép |
|---|---|---|---|
| `skills/autovideo-toolkit/scripts/nen-video.py` | Nén video CRF 20 | autovideo-master | Tự viết, thuộc repo này |

---

## Tóm tắt rủi ro pháp lý còn tồn đọng

1. **63 file SFX:** Repo gốc `sontyphu/autovideo-effects` công khai trên GitHub nhưng KHÔNG ghi rõ nguồn gốc và giấy phép từng file âm thanh. Nếu muốn chắc chắn, cần hỏi tác giả hoặc thay bằng nguồn có giấy phép rõ ràng (Pixabay Audio, Mixkit).
2. **7 file BGM:** Các bản nhạc được cho là từ YouTube Audio Library nhưng chưa xác nhận từng bản trên trang chính thức.
3. **5 file kiểu chữ JSON** (`kieu-chu/*.json`): Đây là file cấu hình kiểu phụ đề, không rõ tác giả có coi là tài sản khóa học hay không. Rủi ro thấp vì chỉ là dữ liệu JSON mô tả font/màu.
