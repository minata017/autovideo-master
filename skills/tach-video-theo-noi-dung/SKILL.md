---
name: tach-video-theo-noi-dung
description: Tách bản ghi, bài giảng hoặc video dài thành các bài học hay clip ngắn có ý nghĩa; lập bảng đoạn giữ, duyệt và xuất hàng loạt.
---

# Tách video theo nội dung

Dùng cùng `tach-video.py` cho hai mục đích: bài học và clip ngắn. Python nằm trong .venv/Scripts/python.exe (Windows) hoặc .venv/bin/python (macOS).

## Quyết định nội dung
1. Xác định mục đích từ yêu cầu. Bài học giữ kiến thức, ví dụ và hỏi đáp liên quan theo trình tự; clip ngắn phải hiểu được khi xem riêng. Không cắt theo thời lượng cố định rồi gọi đó là chia theo chủ đề.
2. `chuan-bi --video FILE [--ten TEN]`. Việc này gửi audio lên Groq; có sự đồng ý cho đúng phạm vi video riêng tư trước khi chạy. Nếu có phiên âm dùng `--transcript FILE`; mốc trong file nhập tính từ đầu phần đã chọn. Lỗi mạng/hạn mức: `tiep-tuc --job DIR`, dùng lại các phần xong.
3. Đọc toàn bộ `loi-giang.txt` hoặc lần lượt tất cả file trong `loi-giang-tung-phan/`. Kiểm tra `can-kiem-tra-phien-am.json`; câu lặp là nghi vấn, không phải bằng chứng chắc chắn. Giữ phiên âm gốc. Nếu xác nhận chữ sai, sửa words trong phien-am.json rồi chạy tiep-tuc để cập nhật bản đọc.
4. Điền `bai-hoc.json` theo mẫu ở [tham chiếu](references/ke-hoach.md). Chọn chủ đề thật, không bịa ý tác giả. Mốc start/end theo video gốc. Một bài có blocks theo thứ tự: video → hoạt động/ghi chú → video; một video có thể giữ nhiều đoạn; chừa ranh giới câu và hơi thở, giữ câu hỏi đi kèm câu trả lời. Nêu rõ phần bỏ và lý do. Không tự loại ví dụ/hỏi đáp chỉ vì muốn video ngắn.
5. `xem-ke-hoach --job DIR` tạo bảng và ảnh đầu/giữa/cuối. Xem ảnh, kiểm tra chữ trên tài liệu, chuyển người nói và đầu/cuối câu. Có thể trích thêm khung hình bằng FFmpeg khi mốc chuyển chưa rõ. Đưa bảng cụ thể cho người dùng duyệt [?].

## Điểm dừng thực hành
- Rà tất cả ranh giới của bảng, không chỉ các mốc người dùng đã chỉ ra. Giữ ví dụ và phản hồi trong cùng bài khi còn chung mạch; đặt lời mời/giới thiệu sát nội dung được dẫn vào.
- Với bản ghi có bài tập: khi bỏ thời gian chờ, tách video trước/sau và giữ chúng trong cùng bài học. Nếu cần xem liên tục thao tác/diễn biến thực hành, giữ khoảng đó trong video. Giữ lời hướng dẫn, lời nhắc có nội dung và phản hồi; nghỉ lấy bút/hơi thở ngắn không tự động thành video riêng.
- Mỗi điểm dừng có khối activity trong blocks: instructions, yêu cầu thực hành/mở trang web/làm bài tập, duration_minutes theo lời giảng hoặc null khi làm đến lúc xong, next_video trong cùng bài và khoảng nguồn rút. Mặc định đặt ghi chú dưới video để dùng khi tạo web, không gắn chữ lên hình. Không lấy độ dài khoảng chờ làm số phút bài tập.
- Phiên âm trống hay câu lặp đáng ngờ không đủ để chốt loại khoảng. Ghi rõ bằng chứng/độ chắc chắn, kiểm tra âm thanh và hình tại khoảng chờ trước khi chốt xuất.

## Xuất và kiểm tra
- Khi bảng đã duyệt: `xuat --job DIR --duyet --muc-dich bai-hoc` hoặc `--muc-dich clip-ngan`.
- Bài học mặc định giữ tỷ lệ/kích thước gốc, phụ đề rời. Clip ngắn mặc định 9:16 crop giữa; xem hình trước vì chưa có theo dõi khuôn mặt/tài liệu. Dùng `--khung goc` khi crop mất nội dung. `--phu-de gan` gắn chữ lên hình nếu phù hợp, `--phu-de roi` giữ hình sạch.
- Chạy lại cùng lệnh để bỏ qua bài đã đạt và phục hồi bài lỗi/mất file. Thay nội dung bảng phải duyệt lại; không dùng kết quả cũ chỉ vì thời lượng giống nhau. Các phiên bản cũ vẫn được giữ.
- Xem tien-do.json, danh-muc.md, cau-truc-bai-hoc.json (bài/video/ghi chú đúng thứ tự) và ket-qua.json từng video. Đo hình/tiếng/phụ đề, xem ảnh và nghe thành phẩm trước khi kết luận chất lượng. Báo đúng phần đã thử, phần cần chủ video duyệt. Không coi việc xuất thành công là nội dung đã được duyệt.
- Chỉ sản xuất file video, phụ đề, ảnh đại diện, danh mục cục bộ. Không tạo website hoặc upload thành phẩm khi người dùng chưa yêu cầu.
