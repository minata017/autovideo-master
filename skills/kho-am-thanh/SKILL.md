---
name: kho-am-thanh
description: Kho 63 hiệu ứng âm thanh (SFX) và 7 bản nhạc nền Piano nhẹ nhàng (BGM), kèm luật chọn tiếng theo tông và liều lượng. Dùng khi cần gắn SFX (chuyển cảnh, chữ hiện, thẻ từ khóa, câu chốt, nói về tiền, cảnh báo) hoặc phối nhạc nền BGM (thiền, spa, bài giảng, tĩnh lặng) vào video.
---

# Kho âm thanh - Hiệu ứng (SFX) & Nhạc nền (BGM)

Thư mục bao gồm hai phần:
- `sfx/`: 63 hiệu ứng âm thanh phân loại theo tiền tố `nhom-mo-ta[-do-dai]` (chuyển cảnh, hiện chữ, click, tiếng tiền, tình huống...).
- `bgm/`: 7 bản nhạc nền Piano YouTube Audio Library miễn phí bản quyền (Aakash Gandhi, Esther Abrami, Wayne Jones) chuyên dùng cho video nhẹ nhàng, thiền, spa, chia sẻ, đào tạo.

## Quy trình 5 bước gắn SFX (làm đúng thứ tự)

**Bước 1 - Bắt TÔNG video trước.** Đọc kịch bản/transcript, xác định tông (truyền cảm hứng / vui / nghiêm túc / cảnh báo / bán hàng / tĩnh tâm) rồi CHỈ chọn tiếng cùng tông - tra bảng tông ở `00-CACH-DUNG.md`. Video nghiêm túc không dùng tiếng giễu cợt.

**Bước 2 - Chỉ chọn điểm ĐẶC BIỆT QUAN TRỌNG.** Tiếng chỉ đi kèm sự kiện thị giác (chuyển cảnh, chữ/thẻ hiện, cảnh phụ vào) - chỉ gắn ở mở chủ đề, khúc quặt, câu chốt. Chuỗi sự kiện lặp cùng loại chỉ gắn cái ĐẦU TIÊN. Video ~30 giây: 3-4 tiếng. Video 1-2 phút: tối đa 5-7. Video màn hình tĩnh chỉ có lời nói: KHÔNG gắn gì.

**Bước 3 - Tra bảng chọn tiếng cụ thể.** Mở `00-DANH-MUC.md`: mỗi tiếng ghi rõ độ dài + đặt vào đoạn nào + dòng nào là MẶC ĐỊNH. Mỗi video chỉ 1 kiểu whoosh + 1 kiểu ding + 1 kiểu pop, lặp có chủ đích.

**Bước 4 - Gắn đúng kỹ thuật.**
- Dò lặng đầu file tiếng bằng `ffmpeg -af silencedetect` rồi cắt (`atrim`).
- Đặt tiếng vào khe lặng giữa các câu (theo mốc transcript), không đè lời nói.
- Âm lượng: tiếng gõ/vụt `volume=0.4-0.5`; tiếng vào êm dần (lung-linh, riser) `0.6-0.7`; luôn thấp hơn lời thoại rõ rệt.
- Trộn bằng `adelay` + `amix=normalize=0`; video sắp hết mà tiếng còn ngân thì thêm `afade=t=out`.

**Bước 5 - Đo bằng chứng.** Sau khi render, đo `volumedetect` 0.3-0.5s tại TỪNG mốc, so bản trước/sau: mốc nào không tăng dB là tiếng chưa vào thật - sửa rồi đo lại. Không nghiệm thu bằng cảm giác.

## Quy tắc phối nhạc nền BGM (Nhẹ nhàng)

1. Khi video có giọng nói, âm lượng BGM đặt ở mức nền rất nhỏ: `-28dB` đến `-32dB` (hoặc `volume=0.08 - 0.12`).
2. Tự động áp dụng Audio Ducking (giảm âm lượng nhạc nền khi có tiếng nói người và tự tăng nhẹ khi im lặng).
3. Luôn fade-in 1-2 giây ở đầu và fade-out 2-3 giây ở cuối video.
