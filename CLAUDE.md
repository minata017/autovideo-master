# autovideo-master - Điều phối biên tập video tự động cho Claude

Hệ thống dựng và biên tập video tự động bằng AI, hoạt động độc lập và điều khiển 100% bằng câu lệnh thoại tiếng Việt tự nhiên trong chat.

---

## 1. Bản đồ công cụ & 4 Skill chuyên sâu

```text
D:\autovideo-master/
├── input/                    # Thả video thô (.mp4, .mov) hoặc kịch bản chữ (.txt)
├── output/                   # Nơi nhận video thành phẩm (9:16 hoặc 16:9)
├── temp/                     # Vùng xử lý dữ liệu trung gian
└── skills/
    ├── autovideo-toolkit/    # Bóc lời Groq LPU, cắt "ờ à", jump-cut, chia clip, nén CRF 20
    ├── kho-am-thanh/         # 63 SFX phân loại theo nhóm + 7 BGM Piano nhẹ nhàng (spa/thiền/học)
    ├── tao-kieu-chu-caption/ # 10 Font việt hóa OFL + 5 kiểu phụ đề (vàng đen, tối giản, shorts)
    └── dung-broll-collage/   # Dựng cảnh B-roll ảnh chuyển động HyperFrames
```

---

## 2. Hai quy trình vận hành cốt lõi

### Quy trình 1: Chỉnh sửa video người nói có sẵn
Khi người dùng đưa video thô vào `input/` và yêu cầu cắt gọt, làm đẹp:
1. **Phiên âm siêu tốc:** Gọi `skills/autovideo-toolkit/scripts/transcribe_groq.py` trích xuất audio và bóc lời thoại qua Groq LPU (`whisper-large-v3-turbo`) -> tạo `temp/transcript.json`.
2. **Dò từ đệm & đoạn lặng:** Chạy `skills/autovideo-toolkit/scripts/tim_tu_dem.py` tìm các đoạn lặng > 0.5s và từ "ờ, à" -> tạo `temp/diem-cat.json`.
3. **Cắt jump-cut không suy hao:** Chạy `skills/autovideo-toolkit/scripts/cat_video.py` cắt bỏ các đoạn thừa, tự động chèn 30ms audio fade mép cắt.
4. **Gắn phụ đề & âm thanh:**
   - Dùng `skills/tao-kieu-chu-caption` gắn phụ đề nhảy chữ (chọn kiểu theo yêu cầu: vàng viền đen, tối giản, in hoa...).
   - Dùng `skills/kho-am-thanh` gắn 3-5 SFX tại các điểm chốt quan trọng (ting, pop, whoosh, money...).
   - Phối BGM nhẹ nhàng (tự động ducking giảm âm lượng khi có tiếng nói).
5. **Nén tự động & Xuất bản:** Chạy `skills/autovideo-toolkit/scripts/nen-video.py` với chuẩn CRF 20 (visually near-lossless) -> xuất file nhẹ, nét căng vào `output/`.

### Quy trình 2: Sản xuất video mới từ kịch bản chữ
Khi người dùng dán kịch bản hoặc thả file `.txt` vào `input/`:
1. **Tạo giọng đọc (Voiceover):** Sử dụng `Edge-TTS` (miễn phí, giọng Hoài My/Nam Minh) hoặc ElevenLabs nếu có API key.
2. **Dựng B-roll:** Phân tích từng câu thoại, gọi `skills/dung-broll-collage` tạo ảnh chuyển động minh họa khớp mốc giây, hoặc lấy B-roll từ `input/broll/` / Pexels API.
3. **Phụ đề & Âm thanh:** Ghép phụ đề phong cách shorts viral và nhạc nền phù hợp.
4. **Nén tự động & Xuất bản:** Tự động nén CRF 20 xuất video hoàn chỉnh vào `output/`.

---

## 3. Các luật cứng AI bắt buộc tuân thủ

1. **Tự động nén 100%:** Mọi video trước khi lưu vào `output/` đều phải chạy qua `nen-video.py` để tối ưu dung lượng mà vẫn giữ nguyên độ nét 1080p/4K. Không chờ người dùng nhắc.
2. **Giữ nguyên gốc trong quá trình cắt:** Tuyệt đối không nén video ở đầu vào để tránh suy giảm chất lượng kép.
3. **Không bịa đường dẫn:** Luôn kiểm tra sự tồn tại của file trong `input/` trước khi chạy lệnh.
4. **Giao tiếp đời thường:** Báo cáo kết quả ngắn gọn, nói rõ vị trí file xuất xưởng trong `output/` kèm dung lượng và tỷ lệ giảm kích thước.
